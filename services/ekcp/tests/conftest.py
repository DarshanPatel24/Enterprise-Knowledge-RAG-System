"""Shared pytest fixtures for the EKCP test suite."""

from __future__ import annotations

import pytest

from config.settings import EkcpSettings


@pytest.fixture
def settings() -> EkcpSettings:
    """Return hermetic EKCP settings that ignore the developer's local .env."""
    return EkcpSettings(_env_file=None)
