"""System APIs — Section 14.9 of the master prompt. Health and readiness
are kept separate on purpose: health says the process is up, readiness
says its dependencies are reachable."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pie_genai import __version__
from pie_genai.config import Settings, get_settings
from pie_genai.api.schemas.system import (
    CapabilitiesResponse,
    HealthResponse,
    ReadinessResponse,
    VersionResponse,
)

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    # No real dependency (Postgres/Redis/PIE Trader) is wired up yet — see
    # docs/architecture/SYSTEM_ARCHITECTURE.md. Each check below is honest
    # about that rather than claiming a connection that doesn't exist.
    checks = {
        "database": "not_configured" if not settings.database_url else "unchecked",
        "redis": "not_configured" if not settings.redis_url else "unchecked",
        "llm_gateway": "not_configured" if not settings.own_genai_endpoint else "unchecked",
    }
    overall = "ok" if all(v != "down" for v in checks.values()) else "degraded"
    return ReadinessResponse(status=overall, checks=checks)


@router.get("/version", response_model=VersionResponse)
async def version(settings: Settings = Depends(get_settings)) -> VersionResponse:
    return VersionResponse(name=settings.app_name, version=__version__, environment=settings.app_env)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(settings: Settings = Depends(get_settings)) -> CapabilitiesResponse:
    return CapabilitiesResponse(
        conversations=False,
        agents=False,
        rag=False,
        memory=False,
        workflows=False,
        pie_trader_integration=False,
        llm_gateway_configured=bool(settings.own_genai_endpoint),
    )
