from __future__ import annotations

from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    version: str
    capabilities: list[str]
    tools_allowed: list[str]
    permission_level: str
    status: str


class AgentHealthResponse(BaseModel):
    id: str
    status: str
    tools_registered: int
    tools_missing: list[str]
