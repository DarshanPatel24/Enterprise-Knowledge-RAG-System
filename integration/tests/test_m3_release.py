"""M3: consolidated release readiness and the go/no-go decision.

Self-contained (no service launches): asserts the release package is complete,
every open risk carries a disposition, no unresolved blocking risk remains, and
the derived decision is GO. Writes the release package and decision record to
``evidence/`` as the final gate artifacts.
"""

from __future__ import annotations

from pathlib import Path

from release.readiness_package import (
    build_release_package,
    render_decision_markdown,
    render_package_markdown,
)

_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"


def test_release_package_is_complete_and_go() -> None:
    package = build_release_package()

    _EVIDENCE_DIR.mkdir(exist_ok=True)
    (_EVIDENCE_DIR / "m3_release_readiness.md").write_text(
        render_package_markdown(package), encoding="utf-8"
    )
    (_EVIDENCE_DIR / "m3_go_no_go.md").write_text(
        render_decision_markdown(package), encoding="utf-8"
    )

    assert package.tracks, "release package must list track statuses"
    assert all(
        track.status in {"approved", "conditional"} for track in package.tracks
    ), "no track may be in a failed state"

    assert package.risks, "release package must record the open-risk register"
    for risk in package.risks:
        assert risk.disposition.strip(), f"risk {risk.risk_id} lacks a disposition"

    assert package.unresolved_blocking == [], "no unresolved blocking risks permitted"
    assert package.decision == "GO"


def test_engine_and_integration_tracks_approved() -> None:
    package = build_release_package()
    by_track = {track.track: track for track in package.tracks}
    for name in ("EKIE", "EKRE", "EKCP", "Web UI"):
        assert by_track[name].status == "approved", f"{name} must be approved"
    assert by_track["Master Integration M1"].status == "approved"
    assert by_track["Master Integration M2"].status == "approved"
