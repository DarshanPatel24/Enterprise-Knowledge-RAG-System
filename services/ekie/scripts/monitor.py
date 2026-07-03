"""Live ingestion progress monitor.

Polls the Control Plane database and renders a real-time terminal dashboard
showing per-document pipeline stage progress, elapsed time, success/failure
counts, and estimated completion. Derives ALL status from the assets table --
the only table written during ingestion; no API call required.

Usage (from any directory):
    python services/ekie/scripts/monitor.py
    python services/ekie/scripts/monitor.py --tenant-id my-tenant --refresh 2
    python services/ekie/scripts/monitor.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

STAGES: list[tuple[str, str]] = [
    ("markdown",     "T"),
    ("intelligence", "I"),
    ("chunks",       "C"),
    ("embedding",    "E"),
    ("vector",       "P"),
]
STAGE_ASSET_TYPES = {a for a, _ in STAGES}
N_STAGES = len(STAGES)


def _elapsed(dt) -> str:
    if dt is None:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    s = int((datetime.now(UTC) - dt).total_seconds())
    if s < 0: return "0s"
    if s < 60: return f"{s}s"
    if s < 3600: return f"{s//60}m {s%60}s"
    return f"{s//3600}h {(s%3600)//60}m"


def _stage_bar(completed: set) -> Text:
    t = Text()
    for asset_type, _ in STAGES:
        if asset_type in completed:
            t.append("x", style="bold green")
        else:
            t.append(".", style="dim white")
        t.append(" ")
    return t


_STAGE_METRICS: list[tuple[str, str, list[tuple[str, str]]]] = [
    # (asset_type, label_prefix, [(key, short_suffix), ...])
    ("markdown",     "T", [("markdown_chars", "ch")]),
    ("intelligence", "I", [("section_count", "§"), ("token_count", "t"),
                            ("table_count", "tbl"), ("language", "")]),
    ("chunks",       "C", [("chunk_count", "ch"), ("total_tokens", "t")]),
    ("embedding",    "E", [("embedding_count", "em"), ("total_tokens", "t"),
                            ("dimension", "d")]),
    ("vector",       "P", [("vector_count", "v"), ("verified_count", "✓")]),
]


def _fmt_metrics(metrics_by_stage: dict[str, dict], completed: set[str]) -> str:
    """Render a compact per-stage metrics summary for completed stages only."""
    parts: list[str] = []
    for asset_type, prefix, fields in _STAGE_METRICS:
        if asset_type not in completed:
            continue
        m = metrics_by_stage.get(asset_type)
        if not m:
            parts.append(f"[dim]{prefix}:?[/dim]")
            continue
        vals: list[str] = []
        for key, suffix in fields:
            v = m.get(key)
            if v is None:
                continue
            if isinstance(v, float):
                s = f"{v:.0f}"
            else:
                s = str(v)
            vals.append(f"{s}{suffix}")
        parts.append(f"{prefix}:{' '.join(vals)}" if vals else f"[dim]{prefix}:?[/dim]")
    return "  ".join(parts)


def _load_snapshot(db, tenant_id: str) -> dict:
    from domain.control_plane.models import Asset, Document
    with db.session() as sess:
        docs = sess.query(Document).filter(Document.tenant_id == tenant_id).order_by(Document.updated_at.desc()).limit(500).all()
        doc_ids = [d.id for d in docs]
        assets = sess.query(Asset).filter(Asset.tenant_id == tenant_id, Asset.document_id.in_(doc_ids), Asset.asset_type.in_(list(STAGE_ASSET_TYPES))).all() if doc_ids else []

        completed_by_doc: dict[str, set[str]] = {d.id: set() for d in docs}
        latest_asset_time: dict[str, datetime] = {}
        # stage_metrics_by_doc: {doc_id: {asset_type: dict}}
        metrics_by_doc: dict[str, dict[str, dict]] = {d.id: {} for d in docs}
        for a in assets:
            completed_by_doc.setdefault(a.document_id, set()).add(str(a.asset_type))
            ts = a.created_at
            if ts:
                if ts.tzinfo is None: ts = ts.replace(tzinfo=UTC)
                prev = latest_asset_time.get(a.document_id)
                if prev is None or ts > prev: latest_asset_time[a.document_id] = ts
            if a.stage_metrics:
                try:
                    metrics_by_doc.setdefault(a.document_id, {})[str(a.asset_type)] = json.loads(a.stage_metrics)
                except (ValueError, TypeError):
                    pass

        rows = []
        for doc in docs:
            completed = completed_by_doc.get(doc.id, set())
            n_done = len(completed)
            is_deleted = str(doc.status) == "deleted"
            if is_deleted: status = "deleted"
            elif n_done == N_STAGES: status = "complete"
            elif n_done > 0: status = "running"
            else: status = "queued"

            current_stage = next((lbl for at, lbl in STAGES if at not in completed), None)
            rows.append({"id": doc.id, "name": Path(doc.source_path).name, "status": status,
                         "completed": completed, "n_done": n_done, "current_stage": current_stage,
                         "doc_updated": doc.updated_at, "last_asset": latest_asset_time.get(doc.id),
                         "is_deleted": is_deleted, "metrics": metrics_by_doc.get(doc.id, {})})

        def _key(r):
            order = {"running": 0, "queued": 1, "complete": 2, "deleted": 3}
            ts = r["last_asset"] or r["doc_updated"]
            return (order.get(r["status"], 9), -(ts.timestamp() if ts else 0))
        rows.sort(key=_key)

        nd = [r for r in rows if not r["is_deleted"]]
        return {"rows": rows, "total": len(nd), "done": sum(1 for r in nd if r["status"]=="complete"),
                "running": sum(1 for r in nd if r["status"]=="running"),
                "queued": sum(1 for r in nd if r["status"]=="queued")}


def _build_header(snap: dict, tenant_id: str, refresh: int) -> Panel:
    total, done, running, queued = snap["total"], snap["done"], snap["running"], snap["queued"]
    pct = int((done/total)*100) if total else 0
    filled = int(pct/5)
    bar = "[bold green]" + "x"*filled + "[/bold green][dim]" + "."*(20-filled) + "[/dim]"
    eta = f"   ~{total-done} remaining" if running > 0 else ""
    body = (f"  Tenant: [cyan]{tenant_id}[/cyan]   Refresh: [dim]{refresh}s[/dim]   "
            f"Time: [dim]{datetime.now().strftime('%H:%M:%S')}[/dim]\n\n"
            f"  {bar}  [bold]{pct}%[/bold]  [bold green]{done}[/bold green] complete  "
            f"[bold yellow]{running}[/bold yellow] running  [dim]{queued}[/dim] queued  "
            f"of [bold]{total}[/bold] total{eta}\n")
    return Panel(body, title="[bold cyan]EKIE Ingestion Monitor[/bold cyan]", border_style="cyan")


def _build_table(snap: dict, show_all: bool) -> Table:
    table = Table(
        show_header=True, header_style="bold cyan", show_lines=True,
        expand=True, padding=(0, 1),
    )
    table.add_column("Document", style="white", max_width=36, no_wrap=True)
    table.add_column("T I C E P", min_width=12, no_wrap=True)
    table.add_column("Status", min_width=18)
    table.add_column("Stage Metrics", min_width=34, no_wrap=True)
    table.add_column("Last", min_width=8, justify="right")

    for r in (snap["rows"] if show_all else snap["rows"][:40]):
        if r["is_deleted"]:
            continue
        bar = _stage_bar(r["completed"])
        last = r["last_asset"] or r["doc_updated"]
        n, cur = r["n_done"], r["current_stage"] or ""
        metrics_str = _fmt_metrics(r.get("metrics", {}), r["completed"])

        if r["status"] == "complete":
            st = Text("complete", style="bold green")
        elif r["status"] == "running":
            # Show how many stages are done and which is next
            st = Text(f">> {cur}  {n}/{N_STAGES} done", style="bold yellow")
        else:
            st = Text("queued", style="dim")

        table.add_row(r["name"], bar, st, metrics_str, _elapsed(last))
    return table


def _build_legend() -> Panel:
    body = (
        "  Stages: [bold green]x[/bold green]=done  [dim].[/dim]=pending  "
        "T=Transform  I=Intelligence  C=Chunking  E=Embedding  P=Publish\n"
        "  Metrics: T=ch(chars)  I=§(sections) t(tokens) tbl(tables) lang"
        "  C=ch(chunks) t(tokens)  E=em(embeds) t(tokens) d(dim)  P=v(vecs) ✓(verified)\n"
        "  [dim]Ctrl+C to exit[/dim]"
    )
    return Panel(body, border_style="dim", padding=(0, 1))


def run_monitor(tenant_id: str, refresh: int, show_all: bool) -> None:
    from config.settings import get_settings
    from domain.control_plane import ControlPlaneDatabase
    db = ControlPlaneDatabase(get_settings().control_plane)
    db.run_migrations()
    with Live(console=console, refresh_per_second=2, screen=True) as live:
        while True:
            try:
                snap = _load_snapshot(db, tenant_id)
                layout = Layout()
                layout.split_column(Layout(_build_header(snap, tenant_id, refresh), size=6),
                                    Layout(_build_table(snap, show_all)),
                                    Layout(_build_legend(), size=3))
                live.update(layout)
                time.sleep(refresh)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                live.update(Panel(f"[red]Error: {exc}[/red]"))
                time.sleep(refresh)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live EKIE ingestion progress monitor")
    parser.add_argument("--tenant-id", default="tenant-default")
    parser.add_argument("--refresh", type=int, default=2)
    parser.add_argument("--all", action="store_true", dest="show_all")
    args = parser.parse_args()
    run_monitor(args.tenant_id, args.refresh, args.show_all)
    console.print("\n[dim]Monitor stopped.[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
