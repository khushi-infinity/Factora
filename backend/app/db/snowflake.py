"""Snowflake connectivity.

Design rules for this module:
  * the connector is imported lazily, so the API boots on a clean clone with no driver, no
    credentials and no network — a missing driver is reported as `unavailable`, not as a crash;
  * credentials live in `Settings` (env / repo-root `.env`) and are never logged, never returned
    to a client, and scrubbed out of any error text that leaves this module (AGENTS rule 4);
  * the probe runs `SELECT 1` only, and its result is cached for `snowflake_probe_ttl_seconds` so
    health polling cannot turn into a session-per-request against the hackathon account
    (AGENTS rule 7: cost discipline).
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from typing import Any, Literal

from ..config import Settings, get_settings

__all__ = ["ProbeResult", "build_connection_params", "probe_snowflake", "reset_probe_cache"]

ProbeState = Literal["ok", "not_configured", "unavailable"]


@dataclass(frozen=True)
class ProbeResult:
    status: ProbeState
    detail: str | None = None
    latency_ms: float | None = None


@dataclass(frozen=True)
class _CachedProbe:
    at: float
    result: ProbeResult


_cache: _CachedProbe | None = None


def reset_probe_cache() -> None:
    """Drop the cached probe result (used by tests and by an explicit `force` probe)."""
    global _cache
    _cache = None


def _scrub(text: str, settings: Settings) -> str:
    """Remove configured credential material from text before it can be surfaced anywhere."""
    scrubbed = text
    for secret in settings.secret_values:
        scrubbed = scrubbed.replace(secret, "[redacted]")
    return scrubbed


def build_connection_params(settings: Settings) -> dict[str, Any]:
    """Connector keyword arguments, with key-pair auth preferred over passwords."""
    params: dict[str, Any] = {
        "account": settings.snowflake_account,
        "user": settings.snowflake_user,
        "role": settings.snowflake_role,
        "warehouse": settings.snowflake_warehouse,
        "database": settings.snowflake_database,
        "schema": settings.snowflake_schema,
        "login_timeout": settings.snowflake_login_timeout_seconds,
        "client_session_keep_alive": settings.snowflake_client_session_keep_alive,
        "session_parameters": {
            "STATEMENT_TIMEOUT_IN_SECONDS": settings.snowflake_query_timeout_seconds,
        },
    }

    if settings.snowflake_private_key_path:
        params["authenticator"] = settings.snowflake_authenticator
        params["private_key_file"] = settings.snowflake_private_key_path
        if settings.snowflake_private_key_passphrase:
            params["private_key_file_pwd"] = settings.snowflake_private_key_passphrase
    else:
        params["authenticator"] = "snowflake"
        params["password"] = settings.snowflake_password

    return {key: value for key, value in params.items() if value is not None}


def _connect(settings: Settings) -> Any:
    import snowflake.connector  # lazy import: keeps API start-up fast and the driver optional

    return snowflake.connector.connect(**build_connection_params(settings))


def probe_snowflake(settings: Settings | None = None, *, force: bool = False) -> ProbeResult:
    """Establish a session and run `SELECT 1`. Never raises; reports state instead."""
    settings = settings or get_settings()

    if not settings.snowflake_configured:
        return ProbeResult("not_configured", "No Snowflake credentials in the environment or .env")

    global _cache
    now = time.time()
    if not force and _cache is not None and now - _cache.at < settings.snowflake_probe_ttl_seconds:
        return _cache.result

    started = time.perf_counter()

    try:
        connection = _connect(settings)
    except ModuleNotFoundError:
        result = ProbeResult("unavailable", "snowflake-connector-python is not installed in this environment")
    except Exception as exc:
        result = ProbeResult("unavailable", _scrub(f"{type(exc).__name__}: {exc}", settings))
    else:
        try:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()
        except Exception as exc:
            result = ProbeResult("unavailable", _scrub(f"{type(exc).__name__}: {exc}", settings))
        else:
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            result = ProbeResult(
                "ok",
                f"Session established with {settings.snowflake_database}.{settings.snowflake_schema}",
                latency_ms,
            )
        finally:
            with contextlib.suppress(Exception):
                connection.close()

    _cache = _CachedProbe(now, result)
    return result
