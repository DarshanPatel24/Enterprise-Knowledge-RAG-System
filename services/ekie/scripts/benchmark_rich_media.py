"""Run a baseline rich-media extraction benchmark on a local folder.

The script scans for rich-media files, runs RichMediaParser extraction,
captures success/failure and text-length metrics, and emits a JSON report.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.transformation.parsers import ParserContext
from domain.transformation.parsers.rich_media import RichMediaParser


SUPPORTED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "tif",
    "tiff",
    "webp",
}


def _dependency_status() -> dict[str, bool]:
    status: dict[str, bool] = {}
    modules = [
        "unstructured",
        "pypdf",
        "docx",
        "pptx",
        "PIL",
        "pytesseract",
    ]
    for module in modules:
        try:
            __import__(module)
            status[module] = True
        except Exception:
            status[module] = False
    status["tesseract_binary"] = shutil.which("tesseract") is not None
    return status


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--output-dir", default="storage")
    parser.add_argument("--max-files", type=int, default=200)
    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    if not target_dir.exists() or not target_dir.is_dir():
        raise SystemExit(f"target directory does not exist: {target_dir}")

    rich_parser = RichMediaParser()
    files = [
        path
        for path in target_dir.rglob("*")
        if path.is_file() and path.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS
    ][: args.max_files]

    results: list[dict[str, object]] = []
    success_count = 0
    failure_count = 0

    for path in files:
        ext = path.suffix.lower().lstrip(".")
        data = path.read_bytes()
        context = ParserContext(
            source_path=str(path),
            extension=ext,
            mime_type="application/octet-stream",
        )
        started = time.perf_counter()
        try:
            parsed = rich_parser.parse(data, context)
            duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
            chars = len(parsed.body)
            success = chars > 0
            success_count += 1 if success else 0
            failure_count += 0 if success else 1
            results.append(
                {
                    "path": str(path),
                    "extension": ext,
                    "success": success,
                    "chars_extracted": chars,
                    "duration_ms": duration_ms,
                    "error": None if success else "empty extraction",
                }
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
            failure_count += 1
            results.append(
                {
                    "path": str(path),
                    "extension": ext,
                    "success": False,
                    "chars_extracted": 0,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                }
            )

    dependency_status = _dependency_status()
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "target_dir": str(target_dir),
        "files_scanned": len(files),
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": 0.0 if not files else round(success_count / len(files), 4),
        "dependency_status": dependency_status,
        "results": results,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"rich_media_benchmark_{_timestamp()}.json"
    output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"RESULT_FILE={output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
