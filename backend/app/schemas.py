"""Response models (the API's public contract).

Every field here is safe to hand to a browser: no credential, key path, account identifier or
user name is ever projected into a response model. If a new field is added, that rule still holds.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DependencyState = Literal["ok", "degraded", "not_configured", "unavailable"]
OverallState = Literal["ok", "degraded"]


class DependencyStatus(BaseModel):
    """State of one upstream dependency, as observed by this process."""

    name: str = Field(description="Dependency identifier, e.g. `snowflake`")
    status: DependencyState
    detail: str | None = Field(
        default=None,
        description="Human-readable note. Never contains credentials or key material.",
    )
    latency_ms: float | None = Field(default=None, description="Probe round-trip time, when a probe ran")


class HealthResponse(BaseModel):
    status: OverallState
    service: str
    version: str
    environment: str
    demo_mode: str
    primary_machine: str = Field(description="Anchor asset for the demo story (display only)")
    time_utc: datetime
    uptime_s: float
    dependencies: list[DependencyStatus]


class LivenessResponse(BaseModel):
    """Cheap liveness answer: no dependencies touched."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
    time_utc: datetime
    uptime_s: float


class RootResponse(BaseModel):
    service: str
    version: str
    milestone: str
    docs: str
    health: str
    note: str
