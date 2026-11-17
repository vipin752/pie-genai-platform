"""Model APIs — Section 14.4. Never exposes provider secrets or internal
infrastructure details; only name/capability metadata and aggregate
usage numbers.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from pie_genai.llm.gateway import LlmGateway

router = APIRouter(prefix="/api/v1/models", tags=["models"])


def _gateway(request: Request) -> LlmGateway:
    return request.app.state.llm_gateway


@router.get("")
async def list_models(request: Request) -> list[dict]:
    gateway = _gateway(request)
    return [
        {
            "name": m.name,
            "provider": m.provider.provider_name,
            "task_types": sorted(m.task_types),
            "context_window_tokens": m.context_window_tokens,
            "supports_structured_output": m.supports_structured_output,
            "supports_streaming": m.supports_streaming,
        }
        for m in gateway.registry.list()
    ]


@router.get("/health")
async def models_health(request: Request) -> dict:
    """A real reachability probe per provider (see ModelProvider.health())
    — for Ollama this is an actual GET /api/tags, not a guess. See
    /api/v1/models/usage's success_rate for the real signal once calls
    are actually being made."""
    gateway = _gateway(request)
    return {
        m.name: {"provider": m.provider.provider_name, "reachable": await m.provider.health()}
        for m in gateway.registry.list()
    }


@router.get("/usage")
async def model_usage(request: Request) -> dict:
    gateway = _gateway(request)
    records = gateway.usage.all()
    by_model: dict[str, dict] = {}
    for m in gateway.registry.list():
        by_model[m.name] = {
            "calls": sum(1 for r in records if r.model == m.name),
            "total_tokens": gateway.usage.total_tokens(m.name),
            "success_rate": gateway.usage.success_rate(m.name),
        }
    return {"models": by_model}
