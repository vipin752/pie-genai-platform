"""Agent APIs — Section 14.3."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from pie_genai.agents.registry import AgentRegistry
from pie_genai.api.schemas.agents import AgentHealthResponse, AgentResponse
from pie_genai.tools.registry import ToolRegistry

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def _registry(request: Request) -> AgentRegistry:
    return request.app.state.agent_registry


def _tool_registry(request: Request) -> ToolRegistry:
    return request.app.state.tool_registry


def _to_response(agent) -> AgentResponse:
    spec = agent.spec
    return AgentResponse(
        id=spec.id,
        name=spec.name,
        description=spec.description,
        domain=spec.domain,
        version=spec.version,
        capabilities=list(spec.capabilities),
        tools_allowed=sorted(spec.tools_allowed),
        permission_level=spec.permission_level.name,
        status=spec.status,
    )


@router.get("", response_model=list[AgentResponse])
async def list_agents(request: Request) -> list[AgentResponse]:
    return [_to_response(a) for a in _registry(request).list()]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, request: Request) -> AgentResponse:
    agent = _registry(request).get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return _to_response(agent)


@router.get("/{agent_id}/health", response_model=AgentHealthResponse)
async def agent_health(agent_id: str, request: Request) -> AgentHealthResponse:
    agent = _registry(request).get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    tools = _tool_registry(request)
    missing = [t for t in agent.spec.tools_allowed if tools.get(t) is None]
    return AgentHealthResponse(
        id=agent.spec.id,
        status="degraded" if missing else agent.spec.status,
        tools_registered=len(agent.spec.tools_allowed) - len(missing),
        tools_missing=sorted(missing),
    )
