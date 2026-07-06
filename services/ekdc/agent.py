import os
import time
import logging
import shutil
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ekdc_agent.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("ekdc.agent")

# Load environment variables from the EKDC-local .env ONLY (never the repo-root
# .env), so paths and the multimodal model always come from services/ekdc/.env
# regardless of the current working directory. override=True makes it authoritative.
_EKDC_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_EKDC_ENV, override=True)

# Reduce third-party console noise so EKDC's own progress logs stand out. These
# libraries otherwise emit HTTP metadata requests and deprecation notices that
# look like errors to users. The env flags must be set BEFORE transformers is
# imported (via converter below) so they take effect.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
# huggingface_hub resets its own logger level at import, so control it via its
# env var (read at import) rather than logging.setLevel. This also silences the
# "unauthenticated requests" warning (set HF_TOKEN in .env to authenticate).
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
for _noisy_logger in ("httpx", "urllib3", "filelock"):
    logging.getLogger(_noisy_logger).setLevel(logging.WARNING)

# Route local model downloads (HuggingFace/transformers/Whisper/torch) to the
# persistent cache folder configured in the EKDC .env (EKDC_MODEL_CACHE_DIR),
# so weights are stored in one predictable place and reused across restarts.
# CRITICAL: this must run BEFORE importing converter, because importing converter
# pulls in docling -> huggingface_hub/transformers, and those libraries resolve
# their cache directories at import time. Configuring the cache afterwards would
# be ignored and downloads would fall back to the default ~/.cache/huggingface.
try:
    from enrichment import configure_model_cache, descriptions_path
    configure_model_cache()
except Exception as _cache_exc:  # never block startup on cache setup
    logger.warning(f"Model cache configuration skipped: {_cache_exc}")

    def descriptions_path(output_path):
        """Fallback used only if enrichment could not be imported."""
        if output_path.endswith(".md"):
            return output_path[:-3] + ".descriptions.json"
        return output_path + ".descriptions.json"

# Heavy import LAST so docling/transformers honor the cache env set above.
from converter import convert_file  # noqa: E402

def _is_within(path, directory):
    """Return True if the absolute path is inside (or equal to) directory.

    Uses commonpath rather than substring matching so that sibling directories
    with shared name prefixes are not treated as nested.
    """
    try:
        path_abs = os.path.abspath(path)
        dir_abs = os.path.abspath(directory)
        return os.path.commonpath([path_abs, dir_abs]) == dir_abs
    except ValueError:
        # Different drives on Windows raise ValueError -> not within.
        return False

def get_output_path(input_path, input_dir, output_dir):
    """
    Computes the corresponding output markdown file path for a given input file.
    Example: input_docs/folder/file.pdf -> output_md/folder/file.pdf.md
    """
    rel_path = os.path.relpath(input_path, input_dir)
    # We append .md to the original filename to avoid collisions (e.g. file.pdf and file.docx)
    out_path = os.path.join(output_dir, f"{rel_path}.md")
    return out_path

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

def _artifacts_dir_for(out_path):
    """Return the Docling image-artifacts folder path for an output .md path.

    Matches converter.py's naming: ``<stem>_artifacts`` where stem is the .md
    filename without its trailing ``.md`` (e.g. ``Test.docx.md`` -> ``Test.docx_artifacts``).
    """
    stem = os.path.splitext(os.path.basename(out_path))[0]
    return os.path.join(os.path.dirname(out_path), f"{stem}_artifacts")

def _remove_output_for(out_path):
    """Remove a document's generated outputs as a unit: the .md, its image
    artifacts folder, and its image-description cache. Best-effort; logs failures.
    """
    removed = False
    if os.path.exists(out_path):
        try:
            os.remove(out_path)
            removed = True
        except OSError as e:
            logger.error(f"Failed to delete {out_path}: {e}")
    artifacts_dir = _artifacts_dir_for(out_path)
    if os.path.isdir(artifacts_dir):
        try:
            shutil.rmtree(artifacts_dir)
            removed = True
        except OSError as e:
            logger.error(f"Failed to delete artifacts {artifacts_dir}: {e}")
    desc_path = descriptions_path(out_path)
    if os.path.exists(desc_path):
        try:
            os.remove(desc_path)
            removed = True
        except OSError as e:
            logger.error(f"Failed to delete descriptions {desc_path}: {e}")
    return removed

def _prune_empty_dirs(start_dir, stop_dir):
    """Remove now-empty directories from start_dir upward, never past stop_dir."""
    current = os.path.abspath(start_dir)
    stop = os.path.abspath(stop_dir)
    while current != stop and _is_within(current, stop):
        try:
            if os.listdir(current):
                break
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)

class EKDCEventHandler(FileSystemEventHandler):
    def __init__(self, input_dir, output_dir):
        super().__init__()
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)

    def on_created(self, event):
        if event.is_directory:
            return
        logger.info(f"File created: {event.src_path}")
        self.process_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        logger.info(f"File modified: {event.src_path}")
        self.process_file(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            # We could clean up empty directories here, but for now we focus on files
            return
        logger.info(f"File deleted: {event.src_path}")
        out_path = get_output_path(event.src_path, self.input_dir, self.output_dir)
        if _remove_output_for(out_path):
            logger.info(f"Removed generated outputs for {event.src_path}")
        _prune_empty_dirs(os.path.dirname(out_path), self.output_dir)

    def on_moved(self, event):
        if event.is_directory:
            return
        logger.info(f"File moved from {event.src_path} to {event.dest_path}")
        
        # Delete old output file
        old_out_path = get_output_path(event.src_path, self.input_dir, self.output_dir)
        if _remove_output_for(old_out_path):
            logger.info(f"Removed old generated outputs for {event.src_path}")
        _prune_empty_dirs(os.path.dirname(old_out_path), self.output_dir)
                
        # Process new file location
        self.process_file(event.dest_path)

    def process_file(self, file_path):
        # Skip symlinks so a link inside the input tree cannot be followed to
        # read or transcode files elsewhere on the host.
        if os.path.islink(file_path):
            logger.warning(f"Skipping symlink: {file_path}")
            return

        file_abs = os.path.abspath(file_path)

        # Feedback-loop guard: never re-process files that live in the output tree.
        if _is_within(file_abs, self.output_dir):
            return

        # Only process files that actually reside within the monitored input tree.
        if not _is_within(file_abs, self.input_dir):
            logger.warning(f"Skipping file outside input directory: {file_path}")
            return

        out_path = get_output_path(file_path, self.input_dir, self.output_dir)

        # Path-traversal guard: the resolved output must stay inside the output tree.
        if not _is_within(os.path.abspath(out_path), self.output_dir):
            logger.warning(f"Refusing output outside output directory for {file_path}")
            return

        ensure_dir(out_path)
        success = convert_file(file_path, out_path)
        if success:
            logger.info(f"Successfully converted {file_path} to {out_path}")
        else:
            logger.error(f"Failed to convert {file_path}")

class EKDCOutputEventHandler(FileSystemEventHandler):
    # Collapse bursts of deletions (e.g. removing a whole *_artifacts folder emits
    # one event per image) into a single regeneration per source document.
    _REGEN_DEBOUNCE_SECONDS = 10

    def __init__(self, input_dir, output_dir, ekdc_handler):
        super().__init__()
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.ekdc_handler = ekdc_handler
        self._last_regen = {}

    def _source_for_output(self, output_path):
        """Map a deleted output file back to its source input file, or None.

        Handles all three generated output kinds: the ``.md`` itself, the
        ``.descriptions.json`` cache, and any image inside a ``<stem>_artifacts``
        folder.
        """
        try:
            rel = os.path.relpath(os.path.abspath(output_path), self.output_dir)
        except ValueError:
            return None
        rel_posix = rel.replace("\\", "/")
        if rel_posix.startswith("../"):
            return None
        if rel.endswith(".md"):
            return os.path.join(self.input_dir, rel[:-3])
        if rel.endswith(".descriptions.json"):
            return os.path.join(self.input_dir, rel[: -len(".descriptions.json")])
        parts = rel_posix.split("/")
        for i, part in enumerate(parts):
            if part.endswith("_artifacts"):
                stem = part[: -len("_artifacts")]
                parent = "/".join(parts[:i])
                rel_stem = f"{parent}/{stem}" if parent else stem
                return os.path.join(self.input_dir, os.path.normpath(rel_stem))
        return None

    def on_deleted(self, event):
        if event.is_directory:
            return

        logger.info(f"Output file deleted: {event.src_path}")

        input_path = self._source_for_output(event.src_path)
        if not input_path:
            return
        # If the source is gone, this deletion is our own cleanup — do not resurrect.
        if not os.path.exists(input_path):
            return
        # Debounce so a burst of deletions regenerates the document only once.
        now = time.monotonic()
        if now - self._last_regen.get(input_path, 0.0) < self._REGEN_DEBOUNCE_SECONDS:
            return
        logger.info(f"Output for {input_path} was deleted; regenerating.")
        self.ekdc_handler.process_file(input_path)
        self._last_regen[input_path] = time.monotonic()

def sync_directories(input_dir, output_dir):
    """
    Performs an initial sync to convert any files that were added/modified
    while the agent was down, and deletes output files for deleted input files.
    """
    input_dir_abs = os.path.abspath(input_dir)
    output_dir_abs = os.path.abspath(output_dir)
    
    # Track which output files correspond to current input files
    valid_output_files = set()
    
    logger.info("Performing initial synchronization...")
    
    for root, _, files in os.walk(input_dir_abs):
        # Skip output dir if inside input dir
        if _is_within(root, output_dir_abs):
            continue
            
        for file in files:
            input_path = os.path.join(root, file)
            out_path = get_output_path(input_path, input_dir_abs, output_dir_abs)
            valid_output_files.add(out_path)
            
            needs_conversion = False
            if not os.path.exists(out_path):
                needs_conversion = True
            else:
                input_mtime = os.path.getmtime(input_path)
                out_mtime = os.path.getmtime(out_path)
                if input_mtime > out_mtime:
                    needs_conversion = True
            
            if needs_conversion:
                logger.info(f"Syncing file: {input_path}")
                ensure_dir(out_path)
                convert_file(input_path, out_path)

    # Cleanup orphaned outputs (input files removed while the agent was down):
    # remove each orphan's .md plus its artifacts folder and description cache.
    # Collect first, then remove, so we don't mutate the tree while walking it.
    orphans = []
    for root, _, files in os.walk(output_dir_abs):
        for file in files:
            if not file.endswith('.md'):
                continue
            out_path = os.path.join(root, file)
            if out_path not in valid_output_files:
                orphans.append(out_path)

    for out_path in orphans:
        logger.info(f"Removing orphaned output for {out_path}")
        _remove_output_for(out_path)
        _prune_empty_dirs(os.path.dirname(out_path), output_dir_abs)

    logger.info("Initial synchronization complete.")

def main():
    input_dir = os.getenv('INPUT_DIRECTORY', 'input_docs')
    output_dir = os.getenv('OUTPUT_DIRECTORY', 'output_md')

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Feedback-loop guard: nested input/output directories can cause generated
    # Markdown to be re-ingested as new input. Warn loudly so operators separate them.
    nested = _is_within(output_dir, input_dir) or _is_within(input_dir, output_dir)
    if nested:
        logger.warning(
            "INPUT_DIRECTORY and OUTPUT_DIRECTORY are nested. This can create a "
            "conversion feedback loop; configure separate directories for safety."
        )

    # Perform initial sync
    sync_directories(input_dir, output_dir)

    # Setup watchdog
    event_handler = EKDCEventHandler(input_dir, output_dir)
    output_event_handler = EKDCOutputEventHandler(input_dir, output_dir, event_handler)
    
    observer = Observer()
    observer.schedule(event_handler, input_dir, recursive=True)
    
    # Also monitor the output directory, but ensure we don't double schedule if output is inside input
    if not nested:
        observer.schedule(output_event_handler, output_dir, recursive=True)
    
    logger.info(f"Starting EKDC Agent.")
    logger.info(f"Monitoring Input Directory: {os.path.abspath(input_dir)}")
    logger.info(f"Monitoring Output Directory: {os.path.abspath(output_dir)}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("EKDC Agent stopping...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
