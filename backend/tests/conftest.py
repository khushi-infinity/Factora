"""Shared pytest fixtures.

The suite must run with **no network and no credentials**, and its result must not depend on a
developer's shell or on their real `.env`. Pydantic-settings gives environment variables priority
over the dotenv file, so:

  * credential variables are pinned to *blank* (→ `None` via the Settings validator), which
    neutralises a real `.env` while keeping the app in its "not configured" state;
  * behavioural variables are pinned to explicit values, so assertions are deterministic instead of
    depending on whatever the developer configured.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.snowflake import reset_probe_cache
from app.main import create_app

# Must never be picked up from a real .env: this suite runs credential-free and offline.
_BLANKED = (
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_PRIVATE_KEY_PATH",
    "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
)

# Pinned for determinism (explicitly NOT blank: a blank CORS list would silently disable CORS).
_PINNED = {
    "APP_ENV": "test",
    "DEMO_MODE": "cache",
    "DEMO_PRIMARY_MACHINE": "CNC-03",
    "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",
}


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for variable in _BLANKED:
        monkeypatch.setenv(variable, "")
    for variable, value in _PINNED.items():
        monkeypatch.setenv(variable, value)

    get_settings.cache_clear()
    reset_probe_cache()
    yield
    get_settings.cache_clear()
    reset_probe_cache()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A fresh application instance per test (settings are read per request, not cached globally)."""
    with TestClient(create_app()) as test_client:
        yield test_client
