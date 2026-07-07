"""Shared pytest fixtures for the EKRE test suite."""

from __future__ import annotations

import pytest

from config.settings import EkreSettings


@pytest.fixture
def settings() -> EkreSettings:
    """Return hermetic EKRE settings that ignore the developer's local .env."""
    return EkreSettings(_env_file=None)
