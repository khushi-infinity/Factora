"""Typed application settings.

Read from the repo-root `.env` (gitignored — AGENTS rule 4) with safe defaults, so a clean clone
boots the API with **no credentials at all** and reports Snowflake as `not_configured` instead of
crashing or inventing data.

Nothing in this module is ever serialised to a client: only `Settings` fields that are explicitly
projected into a response model leave the process (see `app/api/health.py`).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Environment-backed configuration. Field names map to upper-case env vars."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- app -----------------------------------------------------------------
    app_env: str = "development"
    service_name: str = "factora-backend"
    service_version: str = "0.1.0"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "info"

    # --- frontend / CORS (comma-separated origins) ---------------------------
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- demo behaviour (PROJECT_SPEC.md §9 fallback policy) -----------------
    demo_mode: str = "live"
    demo_primary_machine: str = "CNC-03"

    # --- Snowflake (credentials come from the environment only) --------------
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_role: str | None = None
    snowflake_warehouse: str | None = None
    # Names follow the build playbook: database FACTORA with RAW / CORE / AI / DOCS schemas.
    snowflake_database: str = "FACTORA"
    snowflake_schema: str = "CORE"
    snowflake_authenticator: str = "SNOWFLAKE_JWT"
    snowflake_private_key_path: str | None = None
    snowflake_private_key_passphrase: str | None = None
    snowflake_password: str | None = None
    snowflake_query_timeout_seconds: int = 30
    snowflake_login_timeout_seconds: int = 10
    snowflake_client_session_keep_alive: bool = True
    # A connectivity probe costs a session: cache its result and reuse it.
    snowflake_probe_ttl_seconds: int = 30

    @field_validator(
        "snowflake_account",
        "snowflake_user",
        "snowflake_role",
        "snowflake_warehouse",
        "snowflake_private_key_path",
        "snowflake_private_key_passphrase",
        "snowflake_password",
        mode="after",
    )
    @classmethod
    def _blank_strings_are_none(cls, value: str | None) -> str | None:
        """Treat an empty env var as unset, so `SNOWFLAKE_ROLE=` never becomes an empty parameter."""
        return value or None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def snowflake_configured(self) -> bool:
        """True only when enough is present to attempt a real connection."""
        has_identity = bool(self.snowflake_account and self.snowflake_user)
        has_credential = bool(self.snowflake_private_key_path or self.snowflake_password)
        return has_identity and has_credential

    @property
    def secret_values(self) -> list[str]:
        """Credential material to scrub from any text that might be surfaced (AGENTS rule 4)."""
        candidates = [
            self.snowflake_password,
            self.snowflake_private_key_passphrase,
            self.snowflake_private_key_path,
        ]
        return [value for value in candidates if value]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Tests clear the cache via `get_settings.cache_clear()`."""
    return Settings()
