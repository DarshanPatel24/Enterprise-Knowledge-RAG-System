import os
import base64
import shutil
import mimetypes
import logging
import tempfile

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    DocumentConverter = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None

# Initialize logger
logger = logging.getLogger("ekdc.converter")


def _bool_env(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_device():
    """Return the compute device for local models: 'cuda' or 'cpu'.

    Controlled by EKDC_DEVICE (default 'auto'):
      - 'auto'      : use the GPU when a CUDA build of torch detects one, else CPU.
      - 'cuda'/'gpu': prefer the GPU, falling back to CPU if none is available.
      - 'cpu'       : force CPU (useful when sharing a small GPU with EKIE).
    """
    pref = os.environ.get("EKDC_DEVICE", "auto").strip().lower()
    if pref == "cpu":
        return "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _build_ocr_options():
    """Return ``(do_ocr, ocr_options|None)`` for the Docling PDF pipeline.

    Defaults to the locally installed Tesseract CLI engine rather than Docling's
    auto-selection, which otherwise downloads large non-English RapidOCR models
    from a remote CDN. Controlled by EKDC_OCR_* environment variables:
      EKDC_OCR_ENABLED (default true), EKDC_OCR_ENGINE (default 'tesseract'),
      EKDC_OCR_LANGUAGES (default 'eng'), EKDC_OCR_FORCE_FULL_PAGE (default false),
      EKDC_TESSERACT_CMD (optional path to the tesseract binary).
    Returns ``(True, None)`` to fall back to Docling's default engine when the
    requested engine's options class is unavailable.
    """
    if not _bool_env("EKDC_OCR_ENABLED", True):
        return False, None

    engine = os.environ.get("EKDC_OCR_ENGINE", "tesseract").strip().lower()
    langs = [
        part.strip()
        for part in os.environ.get("EKDC_OCR_LANGUAGES", "eng").split(",")
        if part.strip()
    ] or ["eng"]
    force_full = _bool_env("EKDC_OCR_FORCE_FULL_PAGE", False)
    tesseract_cmd = os.environ.get("EKDC_TESSERACT_CMD", "").strip()

    try:
        from docling.datamodel import pipeline_options as po

        if engine in ("tesseract", "tesseract_cli", "tesseractcli"):
            options = po.TesseractCliOcrOptions(lang=langs, force_full_page_ocr=force_full)
            if tesseract_cmd:
                options.tesseract_cmd = tesseract_cmd
        elif engine == "tesserocr":
            options = po.TesseractOcrOptions(lang=langs, force_full_page_ocr=force_full)
        elif engine in ("rapidocr", "rapid"):
            options = po.RapidOcrOptions(force_full_page_ocr=force_full)
        elif engine in ("easyocr", "easy"):
            options = po.EasyOcrOptions(force_full_page_ocr=force_full)
        else:  # 'auto' or unknown -> let Docling pick its default engine
            return True, None
        return True, options
    except Exception as exc:  # docling API differences across versions
        logger.warning(f"OCR engine '{engine}' unavailable ({exc}); using Docling default OCR")
        return True, None

# Load whisper model globally so it's not reloaded for every file
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None and whisper is not None:
        model_name = os.environ.get("EKDC_WHISPER_MODEL", "base").strip() or "base"
        try:
            from enrichment import whisper_cache_dir
            download_root = whisper_cache_dir()
        except Exception:
            download_root = None
        # Honor the offline lockdown: Whisper downloads from a remote CDN and does
        # NOT respect HF_HUB_OFFLINE, so guard it explicitly. If offline and the
        # model is not already cached, skip transcription instead of downloading.
        if _bool_env("EKDC_OFFLINE", False):
            cached = bool(download_root) and os.path.exists(
                os.path.join(download_root, f"{model_name}.pt")
            )
            if not cached:
                logger.warning(
                    f"EKDC_OFFLINE is set and Whisper model '{model_name}' is not cached; "
                    "skipping transcription (no download)."
                )
                return None
        logger.info(f"Loading Whisper '{model_name}' model...")
        device = _resolve_device()
        logger.info(f"Whisper compute device: {device}")
        try:
            if download_root:
                whisper_model = whisper.load_model(
                    model_name, device=device, download_root=download_root
                )
            else:
                whisper_model = whisper.load_model(model_name, device=device)
        except Exception as exc:
            logger.error(f"Could not load Whisper model '{model_name}': {exc}")
            return None
    return whisper_model

def _relativize_image_links(output_path):
    """Rewrite Docling's absolute artifact image paths to relative, /-slash links.

    Docling's ``save_as_markdown`` can emit absolute OS paths (with backslashes)
    for referenced images. This makes them relative to the .md and uses forward
    slashes so links stay portable and render in Markdown viewers.
    """
    try:
        abs_out_dir = os.path.dirname(os.path.abspath(output_path))
        stem = os.path.splitext(os.path.basename(output_path))[0]
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for prefix in (abs_out_dir + os.sep, abs_out_dir + "/", abs_out_dir + "\\"):
            content = content.replace(prefix, "")
        content = content.replace(f"{stem}_artifacts\\", f"{stem}_artifacts/")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as exc:
        logger.warning(f"Could not relativize image links in {output_path}: {exc}")


def _build_docling_converter():
    """Build a DocumentConverter configured to rasterize embedded pictures.

    Falls back to a default converter if the installed Docling version exposes a
    different pipeline-options API, so conversion never fails on config alone.
    """
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2.0
        # Run Docling's layout/table ML models on the GPU when available. Wrapped
        # so version differences in the accelerator API never break conversion.
        try:
            from docling.datamodel.accelerator_options import (
                AcceleratorDevice,
                AcceleratorOptions,
            )

            device = _resolve_device()
            accel_device = (
                AcceleratorDevice.CUDA if device == "cuda" else AcceleratorDevice.CPU
            )
            pipeline_options.accelerator_options = AcceleratorOptions(device=accel_device)
            logger.info(f"Docling compute device: {device}")
        except Exception as exc:  # older docling without accelerator_options
            logger.warning(
                f"Docling accelerator options unavailable ({exc}); using its default device"
            )
        # Pin OCR to the locally installed engine (Tesseract by default) so scanned
        # PDFs are read without Docling silently downloading remote OCR models.
        do_ocr, ocr_options = _build_ocr_options()
        pipeline_options.do_ocr = do_ocr
        if ocr_options is not None:
            pipeline_options.ocr_options = ocr_options
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
    except Exception as exc:  # docling API differences across versions
        logger.warning(
            f"Docling image pipeline config unavailable ({exc}); using default converter"
        )
        return DocumentConverter()


def _resolve_image_mode():
    """Return (ImageRefMode|None, mode_name) from EKDC_DOCLING_IMAGE_MODE.

    Modes: 'referenced' (default; images saved beside the .md and linked),
    'embedded' (base64 inline), 'placeholder' (legacy: drop images).
    """
    mode_name = os.environ.get("EKDC_DOCLING_IMAGE_MODE", "referenced").strip().lower()
    try:
        from docling_core.types.doc import ImageRefMode
    except Exception:
        return None, mode_name
    mapping = {
        "referenced": getattr(ImageRefMode, "REFERENCED", None),
        "embedded": getattr(ImageRefMode, "EMBEDDED", None),
        "placeholder": getattr(ImageRefMode, "PLACEHOLDER", None),
    }
    return mapping.get(mode_name, mapping.get("referenced")), mode_name


def convert_document_docling(input_path, output_path):
    if DocumentConverter is None:
        logger.error("docling is not installed. Cannot convert document.")
        return False

    try:
        converter = _build_docling_converter()
        result = converter.convert(input_path)
        document = result.document
        ref_mode, mode_name = _resolve_image_mode()

        # Referenced mode: let Docling write the .md plus an artifacts folder of
        # extracted images alongside it (keeps the markdown clean for RAG).
        if (
            ref_mode is not None
            and mode_name == "referenced"
            and hasattr(document, "save_as_markdown")
        ):
            from pathlib import Path

            try:
                document.save_as_markdown(Path(output_path), image_mode=ref_mode)
                _relativize_image_links(output_path)
                return True
            except TypeError:
                # Older Docling save_as_markdown without an image_mode parameter;
                # fall through to export-based writing below.
                logger.warning("Docling save_as_markdown lacks image_mode; using export fallback")

        # Embedded / placeholder (or older Docling without save_as_markdown).
        try:
            if ref_mode is not None:
                markdown_text = document.export_to_markdown(image_mode=ref_mode)
            else:
                markdown_text = document.export_to_markdown()
        except TypeError:
            # Older Docling without an image_mode parameter.
            markdown_text = document.export_to_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        return True
    except Exception as e:
        message = str(e)
        if "PDFium" in message or "could not load" in message or "not valid" in message:
            logger.error(
                f"Docling could not load {input_path}: the file appears corrupt, "
                f"encrypted, or not a valid PDF ({message})"
            )
        else:
            logger.error(f"Docling conversion failed for {input_path}: {e}")
        return False

def _write_image_reference(input_path, output_path):
    """Return Markdown that carries the source image into the output.

    Honors EKDC_DOCLING_IMAGE_MODE (shared with Docling): 'referenced' copies the
    image beside the .md and links it, 'embedded' inlines base64, 'placeholder'
    omits the image. Returns '' when the image cannot be carried.
    """
    mode = os.environ.get("EKDC_DOCLING_IMAGE_MODE", "referenced").strip().lower()
    basename = os.path.basename(input_path)
    mime_type, _ = mimetypes.guess_type(input_path)
    mime_type = mime_type or "image/png"

    if mode == "placeholder":
        return ""
    if mode == "embedded":
        try:
            with open(input_path, "rb") as img:
                encoded = base64.b64encode(img.read()).decode("ascii")
            return f"![{basename}](data:{mime_type};base64,{encoded})"
        except Exception as exc:
            logger.warning(f"Could not embed image {input_path}: {exc}")
            return ""
    # referenced (default): copy the image into an artifacts folder beside the .md.
    try:
        out_dir = os.path.dirname(output_path)
        stem = os.path.splitext(os.path.basename(output_path))[0]  # strips trailing .md
        artifacts_dir = os.path.join(out_dir, f"{stem}_artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        shutil.copy2(input_path, os.path.join(artifacts_dir, basename))
        return f"![{basename}]({stem}_artifacts/{basename})"
    except Exception as exc:
        logger.warning(f"Could not copy image {input_path}: {exc}")
        return ""


def convert_image_ocr(input_path, output_path):
    if pytesseract is None or Image is None:
        logger.error("pytesseract or Pillow is not installed. Cannot perform OCR on image.")
        return False

    try:
        image = Image.open(input_path)
        text = pytesseract.image_to_string(image)
        basename = os.path.basename(input_path)
        image_md = _write_image_reference(input_path, output_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Image: {basename}\n\n")
            if image_md:
                f.write(f"{image_md}\n\n")
            f.write("## Extracted Text\n\n")
            f.write(text.strip() or "_No text detected._")
        return True
    except Exception as e:
        logger.error(f"Image OCR failed for {input_path}: {e}")
        return False

def convert_audio_whisper(input_path, output_path):
    model = get_whisper_model()
    if model is None:
        logger.error("Whisper is not installed. Cannot transcribe audio.")
        return False
    
    try:
        result = model.transcribe(input_path)
        text = result['text']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Audio Transcription: {os.path.basename(input_path)}\n\n")
            f.write(text.strip())
        return True
    except Exception as e:
        logger.error(f"Audio transcription failed for {input_path}: {e}")
        return False

def convert_video_to_audio_then_whisper(input_path, output_path):
    if VideoFileClip is None:
        logger.error("moviepy is not installed. Cannot extract audio from video.")
        return False

    # Extract audio to a private temp file in the system temp dir. Writing next to
    # the source (input tree) risks races, permission issues, and re-triggering the
    # watcher; a dedicated temp file avoids leaking artifacts into monitored folders.
    fd, audio_path = tempfile.mkstemp(suffix=".wav", prefix="ekdc_audio_")
    os.close(fd)
    try:
        # Extract audio
        video = VideoFileClip(input_path)
        if video.audio is None:
            logger.warning(f"No audio track found in {input_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Video Transcription: {os.path.basename(input_path)}\n\n(No audio track found in video)")
            return True
            
        video.audio.write_audiofile(audio_path, logger=None)
        
        # Transcribe audio
        success = convert_audio_whisper(audio_path, output_path)
        return success
    except Exception as e:
        logger.error(f"Video transcription failed for {input_path}: {e}")
        return False
    finally:
        # Cleanup temp audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError as exc:
                logger.warning(f"Could not remove temp audio file {audio_path}: {exc}")

def convert_text_to_markdown(input_path, output_path):
    try:
        # We can format it as a code block based on extension or just plain text
        ext = os.path.splitext(input_path)[1].lower().replace('.', '')
        if not ext:
            ext = 'text'

        # Stream the file in chunks instead of reading it all into memory, so
        # arbitrarily large text/code/log files are converted with bounded memory
        # (shutil.copyfileobj reads/writes lazily in fixed-size blocks).
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as src, \
                open(output_path, 'w', encoding='utf-8') as dst:
            dst.write(f"```{ext}\n")
            shutil.copyfileobj(src, dst)
            dst.write("\n```")
        return True
    except Exception as e:
        logger.error(f"Text conversion failed for {input_path}: {e}")
        return False

def convert_file(input_path, output_path):
    """
    Intelligently determines the file type and converts it to markdown.
    """
    if not os.path.exists(input_path):
        logger.error(f"File not found: {input_path}")
        return False

    # DoS guard: skip files larger than the configured limit. Prevents a single
    # oversized (or hostile) file from exhausting memory/CPU. 0 disables the check.
    try:
        max_mb = float(os.environ.get("EKDC_MAX_FILE_SIZE_MB", "1024"))
    except ValueError:
        max_mb = 1024.0
    if max_mb > 0:
        try:
            size_mb = os.path.getsize(input_path) / (1024 * 1024)
            if size_mb > max_mb:
                logger.warning(
                    f"Skipping {input_path}: {size_mb:.1f} MB exceeds "
                    f"EKDC_MAX_FILE_SIZE_MB={max_mb}"
                )
                return False
        except OSError:
            pass

    mime_type, _ = mimetypes.guess_type(input_path)
    ext = os.path.splitext(input_path)[1].lower()
    
    # Docling supported extensions
    docling_exts = ['.pdf', '.docx', '.pptx', '.html', '.htm', '.csv']
    
    # Image extensions for OCR
    image_exts = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    
    # Audio extensions
    audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
    
    # Video extensions
    video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    
    # Text/Code extensions
    text_exts = ['.txt', '.py', '.json', '.xml', '.md', '.log', '.csv', '.tsv']
    
    logger.info(f"Converting {input_path} (MIME: {mime_type}, Ext: {ext})")
    
    try:
        if ext in docling_exts:
            success = convert_document_docling(input_path, output_path)
        elif ext in image_exts or (mime_type and mime_type.startswith('image/')):
            success = convert_image_ocr(input_path, output_path)
        elif ext in audio_exts or (mime_type and mime_type.startswith('audio/')):
            success = convert_audio_whisper(input_path, output_path)
        elif ext in video_exts or (mime_type and mime_type.startswith('video/')):
            success = convert_video_to_audio_then_whisper(input_path, output_path)
        elif ext in text_exts or (mime_type and mime_type.startswith('text/')):
            # Special case for CSV - docling handles it, but just in case it was missed
            if ext == '.csv':
                success = convert_document_docling(input_path, output_path)
            else:
                success = convert_text_to_markdown(input_path, output_path)
        else:
            # Fallback for unknown extensions, try to read as text
            logger.warning(f"Unknown file type for {input_path}, attempting to read as plain text.")
            success = convert_text_to_markdown(input_path, output_path)

        # Optional, opt-in enrichment (metadata front-matter + image descriptions).
        # Never fails the conversion: post-processing swallows its own errors.
        if success:
            try:
                from enrichment import post_process_markdown
                post_process_markdown(input_path, output_path)
            except Exception as exc:
                logger.warning(f"Enrichment skipped for {output_path}: {exc}")
        return success

    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}")
        return False
