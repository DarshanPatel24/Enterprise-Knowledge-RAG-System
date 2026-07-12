"""Live smoke test for the full EKRE retrieval endpoint.

Sends one query to a running EKRE service (``POST /v1/query/retrieve``) and
prints the reranked context package so an operator can verify, by eye, that the
retriever returns correct chunks after reranking. Uses only the standard library
so it runs from any environment without extra dependencies.

Prerequisites:
  * EKRE is running (``python scripts/start_api.py``) against a live Qdrant that
    EKIE has already published into.
  * The ``--clearance`` must be at or above the documents' classification, or the
    pre-pool security filter returns zero candidates. EKIE's default ingestion
    classification is ``internal``; use ``restricted`` to widen the view fully.

Examples (PowerShell):
  python scripts/smoke_retrieve.py --query "how do I reset my password?"
  python scripts/smoke_retrieve.py -q "vacation policy" --clearance restricted
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-q", "--query", required=True, help="The query to retrieve for.")
    parser.add_argument(
        "--url",
        default="http://localhost:8002",
        help="EKRE base URL (default: http://localhost:8002).",
    )
    parser.add_argument(
        "--tenant",
        default="tenant-default",
        help="Tenant id sent as X-Tenant-ID and in the security context.",
    )
    parser.add_argument(
        "--clearance",
        default="internal",
        choices=("public", "internal", "confidential", "restricted"),
        help="Caller clearance; must be >= the documents' classification.",
    )
    parser.add_argument("--user", default="local-user", help="Security-context user id.")
    parser.add_argument("--language", default=None, help="Optional query language hint.")
    parser.add_argument(
        "--snippet",
        type=int,
        default=200,
        help="Max characters of each chunk's content to print (default: 200).",
    )
    parser.add_argument(
        "--raw", action="store_true", help="Also print the full raw JSON response."
    )
    return parser.parse_args()


def _post(url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=120.0) as response:  # noqa: S310 - local URL
        return json.loads(response.read().decode("utf-8"))


def _print_candidates(candidates: list[dict[str, object]], snippet: int) -> None:
    if not candidates:
        print("\n  NO CANDIDATES RETURNED.")
        print("  Likely causes: clearance below the documents' classification")
        print("  (try --clearance restricted), no matching chunks, or a tenant mismatch.")
        return
    print(f"\n  {len(candidates)} candidate(s), ordered by post-rerank relevance:\n")
    for rank, candidate in enumerate(candidates, start=1):
        citation = candidate.get("citation", {}) or {}
        score = candidate.get("relevance_score", 0.0)
        explanation = candidate.get("explanation") or ""
        content = str(candidate.get("content", "")).replace("\n", " ").strip()
        if len(content) > snippet:
            content = content[:snippet] + "..."
        print(f"  #{rank}  score={score:.4f}  [{explanation}]")
        print(f"       doc={citation.get('document_id')}  chunk={citation.get('chunk_id')}")
        print(f"       source={citation.get('source_path')}")
        print(f"       {content}\n")


def _print_trace(trace: dict[str, object]) -> None:
    stages = trace.get("stages", []) or []
    if not stages:
        return
    print("  Stage latencies (ms):")
    for stage in stages:
        print(f"    {str(stage.get('stage')):<20} {float(stage.get('duration_ms', 0.0)):>10.1f}")
    total = float(trace.get("total_ms", 0.0))
    budget = float(trace.get("budget_ms", 0.0))
    flag = "  OVER BUDGET" if trace.get("over_budget") else ""
    print(f"    {'TOTAL':<20} {total:>10.1f}  (budget {budget:.0f}){flag}")


def main() -> int:
    """Run one live retrieval and print the reranked chunks; return an exit code."""
    args = _parse_args()
    endpoint = f"{args.url.rstrip('/')}/v1/query/retrieve"
    correlation_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": args.tenant,
        "X-Correlation-ID": correlation_id,
    }
    payload: dict[str, object] = {
        "query": args.query,
        "security_context": {
            "user_id": args.user,
            "tenant_id": args.tenant,
            "classification_clearance": args.clearance,
        },
    }
    if args.language:
        payload["language"] = args.language

    print(f"POST {endpoint}")
    print(f"  tenant={args.tenant}  clearance={args.clearance}  correlation_id={correlation_id}")
    print(f"  query={args.query!r}")

    try:
        result = _post(endpoint, payload, headers)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"\nHTTP {exc.code} {exc.reason}\n{body}", file=sys.stderr)
        return 2
    except urllib.error.URLError as exc:
        print(f"\nCONNECTION FAILED: {exc.reason}", file=sys.stderr)
        print("Is EKRE running on the given --url?", file=sys.stderr)
        return 2

    package = result.get("package", {}) or {}
    candidates = package.get("candidates", []) or []
    _print_candidates(candidates, args.snippet)
    _print_trace(result.get("trace", {}) or {})

    if args.raw:
        print("\n  Raw response:")
        print(json.dumps(result, indent=2))

    return 0 if candidates else 1


if __name__ == "__main__":
    raise SystemExit(main())
