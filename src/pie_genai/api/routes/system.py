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
        # True = conversation/message/run lifecycle exists and is wired to
        # the model gateway end to end. It does NOT mean a submitted
        # message gets a real answer - the one configured model is an
        # unimplemented skeleton, so every run fails today. See
        # docs/architecture/SYSTEM_ARCHITECTURE.md.
        conversations=True,
        # One real agent (Market Intelligence) exists, wired to 2 real
        # tools. "True" means the agent/tool framework is real and
        # callable end to end - not that every answer succeeds (a tool
        # call still fails honestly if the gateway is unreachable).
        agents=True,
        rag=False,
        memory=False,
        workflows=False,
        # True = the read-only integration adapter exists (trade-card/
        # dashboard/positions/risk). It says nothing about whether the
        # gateway is actually reachable right now — see
        # GET /api/v1/integrations/pie-trader/health for that.
        pie_trader_integration=True,
        llm_gateway_configured=bool(settings.own_genai_endpoint),
    )
