"""Multi-tenant admission control (handbook Chapter 30.8).

Tenant-aware concurrency admission so no single tenant can exhaust shared
retrieval capacity. All execution metadata carries tenant context; this limiter
enforces a per-tenant concurrency ceiling. A ceiling of ``0`` means unlimited.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager


class TenantConcurrencyLimiter:
    """Enforces a per-tenant maximum of concurrent in-flight retrievals."""

    def __init__(self, max_concurrent: int) -> None:
        self._max_concurrent = max_concurrent
        self._active: dict[str, int] = {}
        self._lock = threading.Lock()

    def acquire(self, tenant_id: str) -> bool:
        """Try to admit a retrieval for ``tenant_id``; return whether admitted."""
        if self._max_concurrent <= 0:
            return True
        with self._lock:
            current = self._active.get(tenant_id, 0)
            if current >= self._max_concurrent:
                return False
            self._active[tenant_id] = current + 1
            return True

    def release(self, tenant_id: str) -> None:
        """Release one in-flight slot for ``tenant_id``."""
        with self._lock:
            current = self._active.get(tenant_id, 0)
            if current > 0:
                self._active[tenant_id] = current - 1

    def active(self, tenant_id: str) -> int:
        """Return the number of in-flight retrievals for ``tenant_id``."""
        with self._lock:
            return self._active.get(tenant_id, 0)

    @contextmanager
    def slot(self, tenant_id: str) -> Iterator[bool]:
        """Context manager yielding whether the tenant was admitted."""
        admitted = self.acquire(tenant_id)
        try:
            yield admitted
        finally:
            if admitted:
                self.release(tenant_id)
