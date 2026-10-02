"""Unit tests for configuration and credential handling."""

from __future__ import annotations

import pytest

from app.config import ENV_FILE, Settings
from app.db.snowflake import _scrub, build_connection_params, probe_snowflake, reset_probe_cache


def test_defaults_are_safe_and_offline() -> None:
    settings = Settings()

    assert settings.snowflake_configured is False
    assert settings.snowflake_database == "FACTORA_DEV"
    assert settings.snowflake_schema == "ANALYTICS"
    assert settings.demo_primary_machine == "CNC-03"


def test_env_file_is_the_repo_root_template_location() -> None:
    """`.env` must be the gitignored sibling of PROJECT_SPEC.md, not a file inside backend/."""
    assert ENV_FILE.name == ".env"
    assert (ENV_FILE.parent / "PROJECT_SPEC.md").is_file()
    assert (ENV_FILE.parent / ".env.example").is_file()


def test_cors_origins_are_split_and_trimmed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://a.example, http://b.example ,")

    assert Settings().cors_origin_list == ["http://a.example", "http://b.example"]


def test_key_pair_auth_is_preferred_over_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "org-account")
    monkeypatch.setenv("SNOWFLAKE_USER", "FACTORA_APP_USER")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "should-be-ignored")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PATH", "/tmp/factora_key.p8")

    settings = Settings()
    params = build_connection_params(settings)

    assert settings.snowflake_configured is True
    assert params["authenticator"] == "SNOWFLAKE_JWT"
    assert params["private_key_file"] == "/tmp/factora_key.p8"
    assert "password" not in params, "a password must never be sent alongside key-pair auth"


def test_blank_optionals_are_treated_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """`SNOWFLAKE_ROLE=` in a .env must mean "no role", not an empty parameter."""
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "org-account")
    monkeypatch.setenv("SNOWFLAKE_USER", "FACTORA_APP_USER")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "pw")
    monkeypatch.setenv("SNOWFLAKE_ROLE", "")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "")

    settings = Settings()
    params = build_connection_params(settings)

    assert settings.snowflake_role is None
    assert settings.snowflake_warehouse is None
    assert params["authenticator"] == "snowflake"
    assert params["session_parameters"] == {"STATEMENT_TIMEOUT_IN_SECONDS": 30}
    assert "role" not in params and "warehouse" not in params


def test_probe_reports_not_configured_without_credentials() -> None:
    """No credentials means no connection attempt — and an honest answer."""
    reset_probe_cache()
    result = probe_snowflake(Settings())

    assert result.status == "not_configured"
    assert result.latency_ms is None


def test_credential_material_is_scrubbed_from_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "sup3r-s3cret")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "passphrase-s3cret")
    settings = Settings()

    scrubbed = _scrub("failed with password=sup3r-s3cret and passphrase-s3cret inside", settings)

    assert "sup3r-s3cret" not in scrubbed
    assert "passphrase-s3cret" not in scrubbed
    assert "[redacted]" in scrubbed
