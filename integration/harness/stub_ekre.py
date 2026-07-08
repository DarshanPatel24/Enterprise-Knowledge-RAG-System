"""A controllable stand-in for EKRE's retrieval endpoint.

Used to validate EKCP's resilience without a real EKRE: the stub returns HTTP 429
(backpressure) for a configurable number of calls, then returns a valid retrieval
package. It runs in-process on an ephemeral port (no engine module collision).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping, Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast


class _StubServer(ThreadingHTTPServer):
    """HTTP server that carries a reference to its owning stub."""

    stub: StubEkre


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        server = cast(_StubServer, self.server)
        stub = server.stub
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        backpressure = stub.consume_failure()
        stub.record_hit()
        if backpressure:
            self._respond(429, {"detail": "backpressure"})
        else:
            self._respond(200, stub.package_body())

    def do_GET(self) -> None:
        self._respond(200, {"status": "ok"})

    def _respond(self, status: int, body: Mapping[str, object]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        """Silence the default per-request logging."""


class StubEkre:
    """A configurable EKRE stand-in returning backpressure then success."""

    def __init__(
        self,
        *,
        failures_before_success: int = 0,
        candidates: Sequence[Mapping[str, object]] | None = None,
    ) -> None:
        self._remaining = failures_before_success
        self._candidates = list(candidates or [])
        self._hits = 0
        self._lock = threading.Lock()
        self._server = _StubServer(("127.0.0.1", 0), _Handler)
        self._server.stub = self
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def package_body(self) -> Mapping[str, object]:
        """Return a TracedRetrieval-shaped body wrapping the configured package."""
        return {
            "package": {
                "query": "stub",
                "tenant_id": "tenant-a",
                "candidates": self._candidates,
                "security_filtered": True,
            }
        }

    @property
    def base_url(self) -> str:
        port = int(self._server.server_address[1])
        return f"http://127.0.0.1:{port}"

    @property
    def hits(self) -> int:
        with self._lock:
            return self._hits

    def consume_failure(self) -> bool:
        """Return True (and decrement) while failures remain, else False."""
        with self._lock:
            if self._remaining > 0:
                self._remaining -= 1
                return True
            return False

    def record_hit(self) -> None:
        with self._lock:
            self._hits += 1

    def start(self) -> StubEkre:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
