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
from typing import TYPE_CHECKING, Any

try:  # Interactive scrolling uses the Windows console keyboard API.
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows fallback (no live scroll)
    msvcrt = None  # type: ignore[assignment]


_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from rich.console import Console  # noqa: E402 - imports follow sys.path bootstrap
from rich.layout import Layout  # noqa: E402
from rich.live import Live  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.text import Text  # noqa: E402

if TYPE_CHECKING:
    from domain.control_plane import ControlPlaneDatabase

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


def _elapsed(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    s = int((datetime.now(UTC) - dt).total_seconds())
    if s < 0:
        return "0s"
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


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
                            ("table_count", "tbl"), ("code_block_count", "cb"),
                            ("language", "")]),
    ("chunks",       "C", [("chunk_count", "ch"), ("total_tokens", "t")]),
    ("embedding",    "E", [("embedding_count", "em"), ("total_tokens", "t"),
                            ("batch_count", "b"), ("dimension", "d")]),
    ("vector",       "P", [("vector_count", "v"), ("verified_count", "✓"),
                            ("batch_count", "b")]),
]


def _fmt_metrics(metrics_by_stage: dict[str, dict], completed: set[str]) -> str:
    """Render per-stage metrics, one completed stage per line for readability."""
    parts: list[str] = []
    for asset_type, prefix, fields in _STAGE_METRICS:
        if asset_type not in completed:
            continue
        m = metrics_by_stage.get(asset_type)
        if not m:
            parts.append(f"[cyan]{prefix}[/cyan]  [dim]?[/dim]")
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
        body = " ".join(vals)
        parts.append(
            f"[cyan]{prefix}[/cyan]  {body}" if vals else f"[cyan]{prefix}[/cyan]  [dim]?[/dim]"
        )
    return "\n".join(parts)


# When a stage has not yet reported live progress, its unit total can be derived
# from the completed prior stage's metrics so the status shows a real count
# (e.g. "P 0/258") instead of an opaque stage index. Maps the current stage's
# asset type to (prior_asset_type, metric_key).
_DERIVED_TOTAL_SOURCE: dict[str, tuple[str, str]] = {
    "embedding": ("chunks", "chunk_count"),
    "vector": ("embedding", "embedding_count"),
}


def _derived_total(current_stage_type: str | None, metrics: dict[str, dict]) -> int | None:
    """Best-effort unit total for a stage that has not reported progress yet."""
    source = _DERIVED_TOTAL_SOURCE.get(current_stage_type or "")
    if source is None:
        return None
    prior_type, key = source
    value = metrics.get(prior_type, {}).get(key)
    return int(value) if isinstance(value, (int, float)) else None



def _load_snapshot(db: ControlPlaneDatabase, tenant_id: str) -> dict[str, Any]:
    from domain.control_plane.models import Asset, Document, IngestionJob, ProcessingState
    with db.session() as sess:
        docs = (
            sess.query(Document)
            .filter(Document.tenant_id == tenant_id)
            .order_by(Document.updated_at.desc())
            .limit(500)
            .all()
        )
        doc_ids = [d.id for d in docs]
        assets = (
            sess.query(Asset)
            .filter(
                Asset.tenant_id == tenant_id,
                Asset.document_id.in_(doc_ids),
                Asset.asset_type.in_(list(STAGE_ASSET_TYPES)),
            )
            .all()
            if doc_ids
            else []
        )
        # Latest job per document (drives queued / failed / dead_letter states).
        job_rows = (
            sess.query(IngestionJob)
            .filter(
                IngestionJob.tenant_id == tenant_id,
                IngestionJob.document_id.in_(doc_ids),
            )
            .order_by(IngestionJob.created_at.asc())
            .all()
            if doc_ids
            else []
        )
        job_by_doc: dict[str, dict[str, Any]] = {}
        for job in job_rows:
            job_by_doc[job.document_id] = {
                "status": str(job.status),
                "attempts": job.attempts,
                "error": job.last_error,
                "priority": job.priority,
                "available_at": job.available_at,
                "created_at": job.created_at,
            }
        # Compute each queued job's position in the worker's claim order
        # (priority desc, then earliest available_at, then oldest created_at) so
        # a waiting/queued document can show how many jobs are ahead of it and
        # when it will resume. Jobs deferred by retry backoff are ordered by
        # when they become due.
        _far = datetime.max.replace(tzinfo=UTC)

        def _aware(dt: datetime | None) -> datetime:
            if dt is None:
                return _far
            return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

        queued_docs = [
            doc_id for doc_id, info in job_by_doc.items()
            if info["status"] == "queued"
        ]
        queued_docs.sort(
            key=lambda d: (
                -(job_by_doc[d]["priority"] or 0),
                _aware(job_by_doc[d]["available_at"]),
                _aware(job_by_doc[d]["created_at"]),
            )
        )
        now_ts = datetime.now(UTC)
        for line_no, doc_id in enumerate(queued_docs, start=1):
            info = job_by_doc[doc_id]
            info["line_no"] = line_no
            avail = _aware(info["available_at"])
            # Seconds until the job is eligible to be claimed (0 when due now).
            info["defer_seconds"] = max(0, int((avail - now_ts).total_seconds()))
        # Intra-stage progress (e.g. embedding chunk counts) per document + stage.
        progress_rows = (
            sess.query(ProcessingState)
            .filter(
                ProcessingState.tenant_id == tenant_id,
                ProcessingState.document_id.in_(doc_ids),
            )
            .all()
            if doc_ids
            else []
        )
        progress_by_doc: dict[str, dict[str, tuple[int, int]]] = {}
        for ps in progress_rows:
            if ps.total is None:
                continue
            progress_by_doc.setdefault(ps.document_id, {})[str(ps.stage)] = (
                int(ps.processed or 0),
                int(ps.total),
            )

        completed_by_doc: dict[str, set[str]] = {d.id: set() for d in docs}
        latest_asset_time: dict[str, datetime] = {}
        # metrics_by_doc: {doc_id: {asset_type: metrics_dict}}
        metrics_by_doc: dict[str, dict[str, dict]] = {d.id: {} for d in docs}
        for a in assets:
            completed_by_doc.setdefault(a.document_id, set()).add(str(a.asset_type))
            ts = a.created_at
            if ts:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                prev = latest_asset_time.get(a.document_id)
                if prev is None or ts > prev:
                    latest_asset_time[a.document_id] = ts
            if a.stage_metrics:
                try:
                    metrics_by_doc.setdefault(a.document_id, {})[str(a.asset_type)] = (
                        json.loads(a.stage_metrics)
                    )
                except (ValueError, TypeError):
                    pass

        rows = []
        for doc in docs:
            completed = completed_by_doc.get(doc.id, set())
            n_done = len(completed)
            is_deleted = str(doc.status) == "deleted"
            job = job_by_doc.get(doc.id)
            job_status = job["status"] if job else None
            if is_deleted:
                status = "deleted"
            elif n_done == N_STAGES:
                status = "complete"
            elif job_status == "dead_letter":
                status = "dead_letter"
            elif job_status == "running":
                # A worker holds this job right now -> genuinely in-flight.
                status = "running"
            elif n_done > 0 and job_status is None:
                # No job row (e.g. synchronous path); assume it is progressing.
                status = "running"
            elif n_done > 0:
                # Partial assets from an earlier attempt, but the job is queued
                # (waiting for a worker) -- not actively running. It resumes at
                # the first incomplete stage when a worker claims it.
                status = "waiting"
            else:
                status = "queued"

            current_stage = next(
                (lbl for at, lbl in STAGES if at not in completed), None
            )
            current_stage_type = next(
                (at for at, lbl in STAGES if at not in completed), None
            )
            stage_progress = progress_by_doc.get(doc.id, {}).get(
                current_stage_type or ""
            )
            rows.append({
                "id": doc.id,
                "name": Path(doc.source_path).name,
                "status": status,
                "completed": completed,
                "n_done": n_done,
                "current_stage": current_stage,
                "current_stage_type": current_stage_type,
                "stage_progress": stage_progress,
                "doc_updated": doc.updated_at,
                "last_asset": latest_asset_time.get(doc.id),
                "is_deleted": is_deleted,
                "metrics": metrics_by_doc.get(doc.id, {}),
                "job_status": job_status,
                "job_attempts": job["attempts"] if job else 0,
                "job_error": job["error"] if job else None,
                "line_no": job.get("line_no") if job else None,
                "defer_seconds": job.get("defer_seconds") if job else None,
            })

        def _key(r: dict[str, Any]) -> tuple[int, float]:
            order = {
                "dead_letter": 0, "running": 1, "waiting": 2, "queued": 3,
                "complete": 4, "deleted": 5,
            }
            ts = r["last_asset"] or r["doc_updated"]
            return (order.get(r["status"], 9), -(ts.timestamp() if ts else 0))
        rows.sort(key=_key)

        nd = [r for r in rows if not r["is_deleted"]]
        return {
            "rows": rows,
            "total": len(nd),
            "done": sum(1 for r in nd if r["status"] == "complete"),
            "running": sum(1 for r in nd if r["status"] == "running"),
            "waiting": sum(1 for r in nd if r["status"] == "waiting"),
            "queued": sum(1 for r in nd if r["status"] == "queued"),
            "dead_letter": sum(1 for r in nd if r["status"] == "dead_letter"),
        }


def _build_header(snap: dict, tenant_id: str, refresh: int) -> Panel:
    total, done, running, queued = snap["total"], snap["done"], snap["running"], snap["queued"]
    waiting = snap.get("waiting", 0)
    dead = snap.get("dead_letter", 0)
    pct = int((done/total)*100) if total else 0
    filled = int(pct/5)
    bar = "[bold green]" + "x"*filled + "[/bold green][dim]" + "."*(20-filled) + "[/dim]"
    eta = f"   ~{total-done} remaining" if (running + waiting + queued) > 0 else ""
    wait_txt = f"  [cyan]{waiting}[/cyan] waiting" if waiting else ""
    dead_txt = f"  [bold red]{dead}[/bold red] dead-letter" if dead else ""
    body = (f"  Tenant: [cyan]{tenant_id}[/cyan]   Refresh: [dim]{refresh}s[/dim]   "
            f"Time: [dim]{datetime.now().strftime('%H:%M:%S')}[/dim]\n\n"
            f"  {bar}  [bold]{pct}%[/bold]  [bold green]{done}[/bold green] complete  "
            f"[bold yellow]{running}[/bold yellow] running{wait_txt}  "
            f"[dim]{queued}[/dim] queued{dead_txt}  "
            f"of [bold]{total}[/bold] total{eta}\n")
    return Panel(body, title="[bold cyan]EKIE Ingestion Monitor[/bold cyan]", border_style="cyan")


def _build_table(window: list[dict]) -> Table:
    table = Table(
        show_header=True, header_style="bold cyan", show_lines=True,
        expand=True, padding=(0, 1),
    )
    # Ratio columns flex to fill the console width; fixed-width columns are
    # capped so the table never overflows the terminal. Long cells wrap onto
    # multiple lines (Document, Status, Stage Metrics) instead of being cropped.
    # Status flexes with a sensible minimum so short states stay on one line and
    # longer ones (e.g. "waiting . resume E") wrap rather than truncate; Stage
    # Metrics is trimmed since its content is compact.
    table.add_column("Document", style="white", ratio=3, overflow="fold")
    table.add_column("T I C E P", width=11, no_wrap=True, justify="center")
    table.add_column("Status", ratio=2, min_width=18, overflow="fold")
    table.add_column("Stage Metrics", ratio=4, overflow="fold")
    table.add_column("Last", width=8, justify="right", no_wrap=True)

    for r in window:
        if r["is_deleted"]:
            continue
        bar = _stage_bar(r["completed"])
        last = r["last_asset"] or r["doc_updated"]
        cur = r["current_stage"] or ""
        metrics_str = _fmt_metrics(r.get("metrics", {}), r["completed"])

        if r["status"] == "complete":
            st = Text("complete", style="bold green")
        elif r["status"] == "dead_letter":
            st = Text(f"dead-letter x{r.get('job_attempts', 0)}", style="bold red")
        elif r["status"] == "waiting":
            # Partially processed on an earlier attempt but now queued; it will
            # resume at the first incomplete stage when a worker is free. The
            # earlier stage's live counter is stale, so show the resume point
            # plus its position in the worker's claim order (and, if deferred by
            # retry backoff, roughly how long until it becomes due).
            st = Text(
                f"waiting \u00b7 resume {cur} {r['n_done']}/{N_STAGES}"
                f"{_queue_hint(r)}",
                style="cyan",
            )
        elif r["status"] == "running":
            # Prefer live intra-stage progress (e.g. embedding/publish batches).
            # Before a stage reports, fall back to a derived unit total from the
            # prior stage's metrics so it reads "P 0/258" rather than a stage
            # index. Only the earliest stages (no prior metrics) show N/stages.
            progress = r.get("stage_progress")
            if progress is not None:
                done_units, total_units = progress
            else:
                derived = _derived_total(r.get("current_stage_type"), r.get("metrics", {}))
                done_units, total_units = (0, derived) if derived else (None, None)
            if total_units:
                pct = int((done_units / total_units) * 100) if total_units else 0
                st = Text(f">> {cur} {done_units}/{total_units} {pct}%", style="bold yellow")
            else:
                st = Text(f">> {cur}  {r['n_done']}/{N_STAGES} done", style="bold yellow")
        else:
            st = Text(f"queued{_queue_hint(r)}", style="dim")

        table.add_row(r["name"], bar, st, metrics_str, _elapsed(last))
    return table


def _queue_hint(r: dict) -> str:
    """Position/ETA suffix for a queued or waiting document.

    Shows where the job sits in the worker's claim order ("next" when it is
    first, otherwise "#N in line") so it is clear how many jobs are ahead. If the
    job is deferred by retry backoff, appends the rough time until it is due.
    """
    line_no = r.get("line_no")
    if not line_no:
        return ""
    place = "next" if line_no == 1 else f"#{line_no} in line"
    defer = r.get("defer_seconds") or 0
    if defer > 0:
        place += f", in {_fmt_duration(defer)}"
    return f"  [{place}]"


def _fmt_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _build_legend() -> Panel:
    # Category labels are padded to a fixed width so the rows line up into a
    # clean left "key" column; the second line of Metrics is a continuation.
    body = (
        "  [bold cyan]Stages [/bold cyan]  [bold green]x[/bold green]=done  "
        "[dim].[/dim]=pending    "
        "T Transform   I Intelligence   C Chunking   E Embedding   P Publish\n"
        "  [bold cyan]Status [/bold cyan]  complete    "
        "[bold yellow]>> E 128/260 49%[/bold yellow] (running: stage + done/total)    "
        "[cyan]waiting[/cyan] ([green]next[/green]/#N in line, resumes)    "
        "queued    [bold red]dead-letter[/bold red] (retries exhausted)\n"
        "  [bold cyan]Metrics[/bold cyan]  "
        "[cyan]T[/cyan] ch=chars    "
        "[cyan]I[/cyan] §=sections t=tokens tbl=tables cb=code +lang    "
        "[cyan]C[/cyan] ch=chunks t=tokens\n"
        "  [cyan]       [/cyan]  "
        "[cyan]E[/cyan] em=embeddings t=tokens b=batches d=dim    "
        "[cyan]P[/cyan] v=vectors ✓=verified b=batches\n"
        "  [bold cyan]Last   [/bold cyan]  time since newest stage asset"
        "                              [dim]Ctrl+C to exit[/dim]"
    )
    return Panel(body, title="[dim]Legend[/dim]", border_style="dim", padding=(0, 1))


def _poll_key() -> str | None:
    """Non-blocking read of a single navigation keystroke (Windows console)."""
    if msvcrt is None or not msvcrt.kbhit():
        return None
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):  # extended key: a second code follows
        code = msvcrt.getwch()
        return {
            "H": "up", "P": "down", "I": "pageup", "Q": "pagedown",
            "G": "home", "O": "end",
        }.get(code)
    low = ch.lower()
    if low == "q":
        return "quit"
    if low == "f":
        return "follow"
    return None


def _row_height(r: dict) -> int:
    """Estimate how many terminal lines a table row occupies.

    Stage Metrics render one line per completed stage; long document names wrap.
    A separator line is added because the table draws lines between rows.
    """
    metric_lines = sum(1 for at, _ in STAGES if at in r["completed"])
    lines = max(metric_lines, 1)
    name_len = len(r["name"])
    if name_len > 40:
        lines = max(lines, 3)
    elif name_len > 22:
        lines = max(lines, 2)
    return lines + 1


def _max_offset(visible: list[dict], available: int) -> int:
    """Largest scroll offset that still fills the viewport with the tail rows."""
    used = 0
    i = len(visible)
    while i > 0:
        h = _row_height(visible[i - 1])
        if used + h > available:
            break
        used += h
        i -= 1
    return i


def _pack_window(visible: list[dict], offset: int, available: int) -> list[dict]:
    """Return the slice of rows starting at ``offset`` that fits the viewport."""
    used = 0
    end = offset
    while end < len(visible):
        h = _row_height(visible[end])
        if used + h > available and end > offset:
            break
        used += h
        end += 1
    return visible[offset:end]


def _build_footer(start: int, shown: int, total: int, follow: bool) -> Text:
    mode = "[green]FOLLOW[/green]" if follow else "[yellow]SCROLL[/yellow]"
    span = f"{start + 1}-{start + shown} of {total}" if total else "0 of 0"
    return Text.from_markup(
        f"  rows {span}   {mode}   "
        "[dim]\u2191/\u2193 PgUp/PgDn Home/End scroll \u00b7 f follow \u00b7 q quit[/dim]"
    )


def run_monitor(tenant_id: str, refresh: int) -> None:
    from config.settings import get_settings
    from domain.control_plane import ControlPlaneDatabase
    db = ControlPlaneDatabase(get_settings().control_plane)
    db.run_migrations()
    offset = 0
    follow = True
    snap: dict[str, Any] | None = None
    next_refresh = 0.0
    with Live(console=console, refresh_per_second=8, screen=True) as live:
        while True:
            try:
                now = time.monotonic()
                if snap is None or now >= next_refresh:
                    snap = _load_snapshot(db, tenant_id)
                    next_refresh = now + refresh
                visible = [r for r in snap["rows"] if not r["is_deleted"]]
                # Reserve lines for header (6), footer (1), legend (7) and the
                # table's own borders/header (~4); the rest holds scrollable rows.
                available = max(2, console.size.height - 18)
                max_off = _max_offset(visible, available)
                if follow:
                    offset = 0
                offset = min(offset, max_off)
                window = _pack_window(visible, offset, available)
                layout = Layout()
                layout.split_column(
                    Layout(_build_header(snap, tenant_id, refresh), size=6),
                    Layout(_build_table(window)),
                    Layout(_build_footer(offset, len(window), len(visible), follow), size=1),
                    Layout(_build_legend(), size=7),
                )
                live.update(layout)

                key = _poll_key()
                if key == "quit":
                    break
                elif key == "up":
                    offset, follow = max(0, offset - 1), False
                elif key == "down":
                    offset, follow = min(max_off, offset + 1), False
                elif key == "pageup":
                    offset, follow = max(0, offset - max(1, len(window))), False
                elif key == "pagedown":
                    offset, follow = min(max_off, offset + max(1, len(window))), False
                elif key == "home":
                    offset, follow = 0, False
                elif key == "end":
                    offset, follow = max_off, False
                elif key == "follow":
                    follow = not follow
                time.sleep(0.05)
            except KeyboardInterrupt:
                break
            except Exception as exc:  # noqa: BLE001 - keep the dashboard alive
                live.update(Panel(f"[red]Error: {exc}[/red]"))
                time.sleep(refresh)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live EKIE ingestion progress monitor")
    parser.add_argument("--tenant-id", default="tenant-default")
    parser.add_argument("--refresh", type=int, default=2)
    parser.add_argument(
        "--all", action="store_true", dest="show_all",
        help="(deprecated) all rows are always shown; use scroll keys instead",
    )
    args = parser.parse_args()
    run_monitor(args.tenant_id, args.refresh)
    console.print("\n[dim]Monitor stopped.[/dim]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
