"""FastAPI application factory.

Run in development:
    cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

The app must boot with an empty environment: no Snowflake credentials, no `.env`, no network.
`create_app()` is a factory so tests can build a fresh instance per case.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .config import get_settings
from .schemas import RootResponse


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Factora API",
        version=settings.service_version,
        description=(
            "Backend-for-frontend for the Factora operational digital twin "
            "(Snowflake CoCo CLI Hackathon 2026 — GCC Edition). "
            "M1 exposes health endpoints only; product endpoints arrive with the Snowflake milestones."
        ),
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")

    @app.get("/", response_model=RootResponse, include_in_schema=False)
    def root() -> RootResponse:
        return RootResponse(
            service=settings.service_name,
            version=settings.service_version,
            milestone="M1 — application scaffold",
            docs="/docs",
            health="/api/health",
            note=(
                "No product endpoints yet. Snowflake credentials, if any, are read from the "
                "repo-root .env by this process alone and are never exposed to clients."
            ),
        )

    return app


app = create_app()
