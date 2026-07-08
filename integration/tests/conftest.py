"""Shared fixtures for the Master Integration suite.

Live engine servers are launched lazily and only for tests that request them, so
the contract-only suites stay fast.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from harness.servers import ServiceHandle, launch_ekcp, launch_ekie, launch_ekre


@pytest.fixture(scope="session")
def ekre_and_ekcp() -> Iterator[dict[str, str]]:
    """Launch EKRE then EKCP (with live knowledge integration) for the session."""
    ekre: ServiceHandle = launch_ekre()
    ekcp: ServiceHandle | None = None
    try:
        ekcp = launch_ekcp()
        yield {"ekre": ekre.base_url, "ekcp": ekcp.base_url}
    finally:
        if ekcp is not None:
            ekcp.stop()
        ekre.stop()


@pytest.fixture(scope="session")
def all_engines(ekre_and_ekcp: dict[str, str]) -> Iterator[dict[str, str]]:
    """Add EKIE to the running EKRE + EKCP pair for whole-platform checks."""
    ekie: ServiceHandle = launch_ekie()
    try:
        yield {**ekre_and_ekcp, "ekie": ekie.base_url}
    finally:
        ekie.stop()
