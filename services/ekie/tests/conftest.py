"""Shared pytest fixtures for EKIE tests."""

from collections.abc import Iterator

import pytest

from config.settings import ControlPlaneSettings
from domain.control_plane import ControlPlaneDatabase


@pytest.fixture
def control_plane_db() -> Iterator[ControlPlaneDatabase]:
    """Provide an isolated in-memory SQLite Control Plane database."""
    settings = ControlPlaneSettings(url="sqlite+pysqlite:///:memory:")
    db = ControlPlaneDatabase(settings)
    db.create_all()
    yield db
    db.drop_all()
