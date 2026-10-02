"""Smoke tests for the M1 API surface — the contract the frontend shell depends on."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_health_is_ok_without_credentials(client: TestClient) -> None:
    """A clean clone must serve health, reporting Snowflake as not configured — not as down."""
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "factora-backend"

    snowflake = next(dep for dep in body["dependencies"] if dep["name"] == "snowflake")
    assert snowflake["status"] == "not_configured"
    assert snowflake["latency_ms"] is None
    assert ".env" in snowflake["detail"]


def test_health_payload_shape_is_stable(client: TestClient) -> None:
    body = client.get("/api/health").json()

    for key in (
        "status",
        "service",
        "version",
        "environment",
        "demo_mode",
        "primary_machine",
        "time_utc",
        "uptime_s",
        "dependencies",
    ):
        assert key in body, f"missing key in health payload: {key}"

    assert isinstance(body["uptime_s"], (int, float))
    # Pinned by tests/conftest.py, so these are exact rather than best-effort.
    assert body["environment"] == "test"
    assert body["demo_mode"] == "cache"
    assert body["primary_machine"] == "CNC-03"


def test_health_probe_can_be_skipped(client: TestClient) -> None:
    body = client.get("/api/health", params={"include_snowflake": "false"}).json()

    assert body["dependencies"][0]["detail"] == "No credentials in the environment or .env"


def test_liveness_touches_no_dependency(client: TestClient) -> None:
    response = client.get("/api/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "dependencies" not in body


def test_root_advertises_docs_and_health(client: TestClient) -> None:
    body = client.get("/").json()

    assert body["docs"] == "/docs"
    assert body["health"] == "/api/health"
    assert "M1" in body["milestone"]


def test_openapi_exposes_both_health_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/health" in paths
    assert "/api/health/live" in paths
    assert "get" in paths["/api/health"]


def test_cors_allows_the_vite_dev_origin(client: TestClient) -> None:
    response = client.get("/api/health/live", headers={"Origin": "http://localhost:5173"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_does_not_echo_an_unknown_origin(client: TestClient) -> None:
    response = client.get("/api/health/live", headers={"Origin": "https://evil.example"})

    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.parametrize(
    "secret",
    ["sup3r-s3cret-password", "key-passphrase-value"],
)
def test_health_never_exposes_credential_material(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, secret: str
) -> None:
    """AGENTS rule 4: credentials must never reach a client, even when configured."""
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "example-account")
    monkeypatch.setenv("SNOWFLAKE_USER", "FACTORA_APP_USER")
    if secret == "sup3r-s3cret-password":
        monkeypatch.setenv("SNOWFLAKE_PASSWORD", secret)
    else:
        monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", secret)

    from app.config import get_settings

    get_settings.cache_clear()

    response = client.get("/api/health", params={"include_snowflake": "false"})

    assert response.status_code == 200
    assert secret not in response.text
    assert "FACTORA_APP_USER" not in response.text
    assert "example-account" not in response.text
