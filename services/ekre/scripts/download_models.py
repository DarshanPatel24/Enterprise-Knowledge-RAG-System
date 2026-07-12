"""One-off model downloader for the local EK-RAG reset.

Downloads the configured embedding (and optional reranker) into a target
HuggingFace cache with offline mode disabled, then the running services can
load them with HF_HUB_OFFLINE=1.

Usage:
    python download_models.py --hf-home <dir> --embedding BAAI/bge-base-en-v1.5 [--reranker BAAI/bge-reranker-base]
"""

from __future__ import annotations

import argparse
import os


def main() -> int:
    parser = argparse.ArgumentParser(description="Download HF models into a cache")
    parser.add_argument("--hf-home", required=True)
    parser.add_argument("--embedding", required=True)
    parser.add_argument("--reranker", default="")
    args = parser.parse_args()

    hf_home = os.path.abspath(args.hf_home)
    os.makedirs(hf_home, exist_ok=True)
    os.environ["HF_HOME"] = hf_home
    os.environ["HF_HUB_OFFLINE"] = "0"
    os.environ["TRANSFORMERS_OFFLINE"] = "0"

    # Imports must follow the env setup so the cache path is honoured.
    from sentence_transformers import SentenceTransformer

    print(f"[download] HF_HOME={hf_home}")
    print(f"[download] embedding={args.embedding}")
    SentenceTransformer(args.embedding)
    print("[download] embedding OK")

    if args.reranker:
        from sentence_transformers import CrossEncoder

        print(f"[download] reranker={args.reranker}")
        CrossEncoder(args.reranker)
        print("[download] reranker OK")

    print("[download] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
