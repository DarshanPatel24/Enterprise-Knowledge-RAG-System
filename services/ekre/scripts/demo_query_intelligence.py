"""Offline demonstration of the EKRE-S1 query intelligence pipeline.

Runs fully offline (no LLM, no retrieval): understands, classifies, enriches, and
plans several example queries, printing the explainable Structured Query Model
and Retrieval Execution Plan for each.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` and the contracts package import when run directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import build_query_intelligence_engine  # noqa: E402
from config.settings import EkreSettings  # noqa: E402

_QUERIES = (
    "compare EKIE and EKRE architecture",
    "everything about refinery shutdown procedures",
    "policy regarding GDPR after:2024",
    'open the latest "VPN Setup Guide"',
)


def main() -> None:
    """Run the offline EKRE-S1 query intelligence demo."""
    engine = build_query_intelligence_engine(EkreSettings(_env_file=None))
    for query in _QUERIES:
        result = engine.analyze(query, tenant_id="tenant-a")
        print("=" * 70)
        print("Query:", query)
        print("  intent:", result.intent.intent.value)
        print("  profile:", result.intent.suggested_profile.value)
        print("  complexity:", result.intent.complexity.value)
        print("  entities:", result.understanding.entities)
        print("  enriched:", result.enrichment.enriched_terms)
        print("  engines:", [step.engine.value for step in result.plan.steps])
        print("  ranking:", result.plan.ranking_strategy.value)
        print("  transformations:")
        for transformation in result.transformations:
            print(f"    - {transformation.stage}: {transformation.description}")


if __name__ == "__main__":
    main()
