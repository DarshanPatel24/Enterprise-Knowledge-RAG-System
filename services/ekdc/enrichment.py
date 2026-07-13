"""Optional enrichment for EKDC output.

Everything here is opt-in via .env and degrades gracefully: if a model or
server is unavailable, enrichment is skipped and the base conversion is kept, so
a document is never lost because enrichment failed.

Toggles (all read from the environment / .env, nothing hardcoded):
  EKDC_INCLUDE_METADATA   (default true)  - prepend a YAML metadata block
  EKDC_DESCRIBE_IMAGES    (default false) - describe images with a VLM
  EKDC_VLM_PROVIDER        (ollama|huggingface, default ollama)
  EKDC_VLM_MODEL           (e.g. qwen2.5vl or Qwen/Qwen2.5-VL-7B-Instruct)
  EKDC_VLM_BASE_URL        (default http://localhost:11434, ollama)
  EKDC_VLM_PROMPT          (default: a search-indexing description prompt)
"""

import os
import re
import json
import time
import base64
import hashlib
import logging
import mimetypes
from datetime import datetime, timezone

logger = logging.getLogger("ekdc.enrichment")

_DEFAULT_VLM_PROMPT = (
    "Describe this image in detail for search indexing. Include any visible text, "
    "charts, diagrams, objects and their relationships. Be concise and factual."
)
# Only enrich local image links (skip data: URIs and remote URLs).
_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*\]\((?!https?://|data:)([^)]+)\)")


def _build_langfuse_client():
    """Return a Langfuse client for tracing, or None when disabled/unavailable.

    Self-hosted and local-first: keys and host come from the EKDC environment.
    Any failure degrades to no tracing so document conversion is never blocked.
    """
    if not _bool_env("EKDC_LANGFUSE_ENABLED", False):
        return None
    public_key = os.environ.get("EKDC_LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("EKDC_LANGFUSE_SECRET_KEY", "").strip()
    host = os.environ.get("EKDC_LANGFUSE_URL", "http://localhost:3000").strip()
    if not public_key or not secret_key:
        logger.warning(
            "EKDC_LANGFUSE_ENABLED is set but the public/secret key is missing; "
            "image-description tracing is disabled"
        )
        return None
    try:
        from langfuse import Langfuse
    except ImportError:
        logger.warning("langfuse is not installed; image-description tracing disabled")
        return None
    try:
        return Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    except Exception as exc:  # client init must never break conversion
        logger.warning(f"Langfuse client init failed; tracing disabled: {exc}")
        return None


def _bool_env(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name, default):
    """Return an int env var, falling back to ``default`` when unset/invalid."""
    try:
        return int(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default


def descriptions_path(output_path):
    """Return the per-document image-description cache path for an output ``.md``.

    Mirrors the Markdown/artifacts layout so the cache lives in the same folder
    structure: ``.../Foo.docx.md`` -> ``.../Foo.docx.descriptions.json`` (next to
    the Markdown). This keeps each document's outputs together and makes them easy
    to remove as a unit when the source file is deleted.
    """
    if output_path.endswith(".md"):
        return output_path[:-3] + ".descriptions.json"
    return output_path + ".descriptions.json"


def file_sha256(path):
    """Return the SHA-256 hex digest of a file, streamed for large files."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- Persistent local-model cache -------------------------------------------

def model_cache_dir():
    """Return (and create) the persistent directory for downloaded local models.

    Uses EKDC_MODEL_CACHE_DIR when set; otherwise defaults to <ekdc>/models so
    weights are stored next to the service and survive restarts. Relative paths
    are resolved against the EKDC service folder (not the current working
    directory) so the location is predictable no matter where the agent starts.
    """
    ekdc_dir = os.path.dirname(os.path.abspath(__file__))
    configured = os.environ.get("EKDC_MODEL_CACHE_DIR", "").strip()
    if configured:
        configured = os.path.expanduser(configured)
        base = configured if os.path.isabs(configured) else os.path.join(ekdc_dir, configured)
        base = os.path.abspath(base)
    else:
        base = os.path.join(ekdc_dir, "models")
    os.makedirs(base, exist_ok=True)
    return base


def whisper_cache_dir():
    """Return (and create) the Whisper subdirectory of the model cache."""
    path = os.path.join(model_cache_dir(), "whisper")
    os.makedirs(path, exist_ok=True)
    return path


def configure_model_cache():
    """Point HuggingFace/transformers/torch downloads at the persistent cache.

    When EKDC_MODEL_CACHE_DIR is set it is authoritative; otherwise the default
    <ekdc>/models is used but any pre-existing HF_HOME is respected.
    """
    base = model_cache_dir()
    hf = os.path.join(base, "huggingface")
    os.makedirs(hf, exist_ok=True)
    explicit = bool(os.environ.get("EKDC_MODEL_CACHE_DIR", "").strip())
    for key, value in (
        ("HF_HOME", hf),
        ("HF_HUB_CACHE", os.path.join(hf, "hub")),
        ("HUGGINGFACE_HUB_CACHE", os.path.join(hf, "hub")),
        ("TRANSFORMERS_CACHE", os.path.join(hf, "transformers")),
        ("TORCH_HOME", os.path.join(base, "torch")),
    ):
        if explicit:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)
    return base


# --- Metadata front-matter ---------------------------------------------------

def _image_dimensions(path):
    try:
        from PIL import Image

        mime, _ = mimetypes.guess_type(path)
        if mime and mime.startswith("image/"):
            with Image.open(path) as im:
                return im.size
    except Exception:
        return None
    return None


def build_metadata_frontmatter(input_path):
    """Return a YAML front-matter block of file metadata, or '' on failure."""
    try:
        stat = os.stat(input_path)
        mime, _ = mimetypes.guess_type(input_path)
        lines = [
            "---",
            f"source_file: {os.path.basename(input_path)}",
            f"source_path: {input_path}",
            f"file_extension: {os.path.splitext(input_path)[1].lower()}",
            f"mime_type: {mime or 'unknown'}",
            f"size_bytes: {stat.st_size}",
            f"created_at: {datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat()}",
            f"modified_at: {datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()}",
            f"content_sha256: {file_sha256(input_path)}",
        ]
        dims = _image_dimensions(input_path)
        if dims:
            lines.append(f"image_width: {dims[0]}")
            lines.append(f"image_height: {dims[1]}")
        lines.append("---")
        return "\n".join(lines) + "\n\n"
    except Exception as exc:
        logger.warning(f"Could not build metadata for {input_path}: {exc}")
        return ""


# --- Multimodal image description -------------------------------------------

class ImageDescriber:
    """Config-driven VLM image describer with per-image caching.

    Provider and model come from the environment (never hardcoded). Ollama uses
    LangChain's ChatOllama (multimodal messages); HuggingFace loads the model
    from the HF hub via transformers (LangChain's text pipeline does not wrap
    vision models). Any failure returns an empty description and is logged.
    """

    def __init__(self, cache_path=None):
        self._provider = os.environ.get("EKDC_VLM_PROVIDER", "ollama").strip().lower()
        self._model = os.environ.get("EKDC_VLM_MODEL", "").strip()
        self._base_url = os.environ.get("EKDC_VLM_BASE_URL", "http://localhost:11434").strip()
        self._prompt = os.environ.get("EKDC_VLM_PROMPT", _DEFAULT_VLM_PROMPT)
        self._max_new_tokens = _int_env("EKDC_VLM_MAX_NEW_TOKENS", 256)
        self._client = None
        self._cache = {}
        # Self-hosted Langfuse tracing for the VLM describe call (opt-in; None
        # when disabled). Tracing failures never block conversion.
        self._langfuse = _build_langfuse_client()
        # Per-document cache when a path is supplied (mirrors the .md/artifacts
        # layout); falls back to a single global file for backward compatibility.
        self._cache_path = cache_path or os.path.join(
            os.environ.get("OUTPUT_DIRECTORY", "."), ".ekdc_image_descriptions.json"
        )
        self._load_cache()

    @staticmethod
    def enabled():
        return _bool_env("EKDC_DESCRIBE_IMAGES", False)

    def _start_span(self, image_path):
        """Start a Langfuse span for one image description, or None if disabled."""
        if self._langfuse is None:
            return None
        try:
            return self._langfuse.start_span(
                name="ekdc.describe_image",
                input={
                    "image": os.path.basename(image_path),
                    "provider": self._provider,
                    "model": self._model,
                    "prompt": self._prompt,
                },
            )
        except Exception:  # tracing must never break conversion
            return None

    def _end_span(self, span, *, output=None, error=None):
        """Finalize a Langfuse span with output or an error, then flush."""
        if span is None:
            return
        try:
            if error is not None:
                span.update(level="ERROR", status_message=str(error))
            else:
                text = output or ""
                span.update(output={"description": text, "chars": len(text)})
            span.end()
            self._langfuse.flush()
        except Exception:  # tracing must never break conversion
            pass

    def describe(self, image_path):
        """Return a description string for ``image_path`` ('' on any failure)."""
        try:
            key = file_sha256(image_path)
        except Exception:
            return ""
        if key in self._cache:
            return self._cache[key]
        span = None
        try:
            if not self._model:
                logger.warning("EKDC_VLM_MODEL is not set; skipping image description")
                return ""
            span = self._start_span(image_path)
            if self._provider == "ollama":
                text = self._describe_ollama(image_path)
            elif self._provider == "huggingface":
                text = self._describe_huggingface(image_path)
            else:
                logger.warning(f"Unknown EKDC_VLM_PROVIDER {self._provider!r}; skipping")
                self._end_span(span, error="unknown provider")
                return ""
        except Exception as exc:
            logger.warning(f"Image description failed for {image_path}: {exc}")
            self._end_span(span, error=exc)
            return ""
        text = (text or "").strip()
        self._end_span(span, output=text)
        self._cache[key] = text
        self._save_cache()
        return text

    def _describe_ollama(self, image_path):
        from langchain_core.messages import HumanMessage
        from langchain_ollama import ChatOllama

        if self._client is None:
            self._client = ChatOllama(
                model=self._model, base_url=self._base_url, temperature=0.0
            )
        mime, _ = mimetypes.guess_type(image_path)
        mime = mime or "image/png"
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        message = HumanMessage(
            content=[
                {"type": "text", "text": self._prompt},
                {"type": "image_url", "image_url": f"data:{mime};base64,{encoded}"},
            ]
        )
        response = self._client.invoke([message])
        content = response.content
        return content if isinstance(content, str) else str(content)

    def _describe_huggingface(self, image_path):
        # Local VLMs are run through transformers (downloaded from the HF hub);
        # LangChain's text pipeline does not wrap vision-language models. Weights
        # go to the persistent model cache (EKDC_MODEL_CACHE_DIR).
        configure_model_cache()
        from transformers import pipeline

        if self._client is None:
            # Secure by default: never execute custom modeling code shipped in a
            # model repo. Operators must consciously opt in via
            # EKDC_VLM_TRUST_REMOTE_CODE=true for models that require it.
            trust_remote_code = _bool_env("EKDC_VLM_TRUST_REMOTE_CODE", False)
            logger.info(
                f"Loading VLM {self._model!r} (transformers); this can take a while "
                f"on first use while weights load into memory..."
            )
            self._client = pipeline(
                "image-text-to-text",
                model=self._model,
                device_map="auto",
                trust_remote_code=trust_remote_code,
            )
            # Set generation length on the model's generation_config so we don't
            # pass conflicting max_length/max_new_tokens kwargs at call time
            # (which emits noisy transformers warnings and can truncate output).
            try:
                gen_cfg = self._client.model.generation_config
                gen_cfg.max_new_tokens = self._max_new_tokens
                gen_cfg.max_length = None
            except Exception:  # generation_config is best-effort tuning only
                pass
            # Report the device so a "stuck" run is recognizable as slow CPU
            # inference rather than a hang. On CPU a multi-billion-parameter VLM
            # can take minutes per image; a GPU is dramatically faster.
            try:
                device = str(getattr(self._client.model, "device", "unknown"))
            except Exception:
                device = "unknown"
            if device.startswith("cpu") or device == "unknown":
                logger.warning(
                    f"VLM {self._model!r} is running on CPU (device={device}); "
                    f"each image can take minutes with EKDC_VLM_MAX_NEW_TOKENS="
                    f"{self._max_new_tokens}. Lower that value or use a GPU/Ollama "
                    f"to speed this up."
                )
            else:
                logger.info(f"VLM {self._model!r} loaded on device={device}")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": image_path},
                    {"type": "text", "text": self._prompt},
                ],
            }
        ]
        result = self._client(text=messages)
        if isinstance(result, list) and result:
            generated = result[0].get("generated_text")
            if isinstance(generated, list) and generated:
                return str(generated[-1].get("content", ""))
            return str(generated or "")
        return str(result)

    def _load_cache(self):
        try:
            if os.path.exists(self._cache_path):
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception:
            pass


def _enrich_image_links(output_path, describer):
    """Append a VLM description after each local image link in the Markdown.

    Descriptions are written back incrementally (after each image) and progress
    is logged, so a long run shows activity and partial results are never lost
    if it is interrupted.
    """
    out_dir = os.path.dirname(os.path.abspath(output_path))
    with open(output_path, "r", encoding="utf-8") as f:
        original = f.read()

    # Unique local image links, in document order.
    ordered_links = []
    for match in _IMAGE_LINK_RE.finditer(original):
        rel = match.group(1).strip()
        if rel not in ordered_links:
            ordered_links.append(rel)
    total = len(ordered_links)
    if total == 0:
        return

    described = {}

    def _replace(match):
        rel = match.group(1).strip()
        text = described.get(rel)
        if not text:
            return match.group(0)
        return f"{match.group(0)}\n\n> **Image description:** {text}"

    for index, rel in enumerate(ordered_links, start=1):
        abs_path = rel if os.path.isabs(rel) else os.path.join(out_dir, rel)
        if not os.path.isfile(abs_path):
            continue
        logger.info(f"Describing image {index}/{total}: {rel}")
        started = time.monotonic()
        desc = describer.describe(abs_path)
        elapsed = time.monotonic() - started
        if not desc:
            logger.info(f"  image {index}/{total}: no description ({elapsed:.1f}s)")
            continue
        preview = desc if len(desc) <= 200 else desc[:200] + "…"
        logger.info(f"  image {index}/{total} described in {elapsed:.1f}s: {preview}")
        described[rel] = desc
        # Rewrite after each successful description so progress is persisted.
        new_content = _IMAGE_LINK_RE.sub(_replace, original)
        if new_content != original:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    logger.info(f"Image descriptions complete: {len(described)}/{total} described")


def post_process_markdown(input_path, output_path):
    """Apply optional enrichment to a freshly written .md (never raises)."""
    try:
        if not os.path.isfile(output_path):
            return
        # 1) Image descriptions (before metadata so front-matter stays at the top).
        if ImageDescriber.enabled():
            try:
                describer = ImageDescriber(cache_path=descriptions_path(output_path))
                _enrich_image_links(output_path, describer)
            except Exception as exc:
                logger.warning(f"Image enrichment skipped for {output_path}: {exc}")
        # 2) Metadata front-matter (prepended, unless the file already has one).
        if _bool_env("EKDC_INCLUDE_METADATA", True):
            front_matter = build_metadata_frontmatter(input_path)
            if front_matter:
                with open(output_path, "r", encoding="utf-8") as f:
                    body = f.read()
                if not body.lstrip().startswith("---"):
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(front_matter + body)
    except Exception as exc:
        logger.warning(f"Enrichment post-processing skipped for {output_path}: {exc}")
