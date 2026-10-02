"""Health endpoints.

`/api/health/live` answers without touching any dependency (safe for a supervisor or a CI smoke
test). `/api/health` additionally reports Snowflake reachability, and is deliberately explicit
about the difference between "not configured" and "unavailable" — the UI must never show a
missing credential as an outage, or an outage as a configuration gap.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter, Query

from ..config import get_settings
from ..db.snowflake import probe_snowflake
from ..schemas import DependencyStatus, HealthResponse, LivenessResponse

router = APIRouter(tags=["health"])

_STARTED_MONOTONIC = time.monotonic()


def _now() -> datetime:
    return datetime.now(UTC)


def _uptime_s() -> float:
    return round(time.monotonic() - _STARTED_MONOTONIC, 3)


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness — no dependencies touched",
)
def liveness() -> LivenessResponse:
    settings = get_settings()
    return LivenessResponse(
        service=settings.service_name,
        version=settings.service_version,
        time_utc=_now(),
        uptime_s=_uptime_s(),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Readiness — application plus Snowflake reachability",
)
def health(
    include_snowflake: bool = Query(
        default=True,
        description="Probe Snowflake (result is TTL-cached). Set false for a pure application check.",
    ),
) -> HealthResponse:
    settings = get_settings()

    if include_snowflake:
        probe = probe_snowflake(settings)
        snowflake = DependencyStatus(
            name="snowflake",
            status=probe.status,
            detail=probe.detail,
            latency_ms=probe.latency_ms,
        )
    else:
        configured = settings.snowflake_configured
        snowflake = DependencyStatus(
            name="snowflake",
            status="ok" if configured else "not_configured",
            detail=(
                "Credentials present; probe skipped on request"
                if configured
                else "No credentials in the environment or .env"
            ),
            latency_ms=None,
        )

    dependencies = [snowflake]
    overall = "degraded" if any(dep.status == "unavailable" for dep in dependencies) else "ok"

    return HealthResponse(
        status=overall,
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.app_env,
        demo_mode=settings.demo_mode,
        primary_machine=settings.demo_primary_machine,
        time_utc=_now(),
        uptime_s=_uptime_s(),
        dependencies=dependencies,
    )
