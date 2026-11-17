from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str


class CapabilitiesResponse(BaseModel):
    """Honest capability flags — see docs/architecture/SYSTEM_ARCHITECTURE.md
    for the full status matrix. Only flip a flag to true once the feature
    is actually implemented and tested, never to match the product vision."""

    conversations: bool
    agents: bool
    rag: bool
    memory: bool
    workflows: bool
    pie_trader_integration: bool
    llm_gateway_configured: bool
