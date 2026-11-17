from __future__ import annotations

from fastapi import FastAPI

from pie_genai import __version__
from pie_genai.agents.market_intelligence_agent import MarketIntelligenceAgent
from pie_genai.agents.registry import AgentRegistry
from pie_genai.api.routes.agents import router as agents_router
from pie_genai.api.routes.conversations import router as conversations_router
from pie_genai.api.routes.models import router as models_router
from pie_genai.api.routes.pie_trader import router as pie_trader_router
from pie_genai.api.routes.runs import router as runs_router
from pie_genai.api.routes.system import router as system_router
from pie_genai.config import Settings, get_settings
from pie_genai.conversations.store import ConversationStore
from pie_genai.core.orchestrator import Orchestrator
from pie_genai.integrations.pie_trader import PieTraderClient
from pie_genai.llm.gateway import build_default_gateway
from pie_genai.tools.execution import ToolExecutor
from pie_genai.tools.pie_trader_tools import build_pie_trader_tools
from pie_genai.tools.registry import ToolRegistry


def _build_agent_registry(settings: Settings) -> tuple[AgentRegistry, ToolRegistry, ToolExecutor]:
    tool_registry = ToolRegistry()
    pie_trader_client = PieTraderClient(
        base_url=settings.pie_trader_gateway_url, api_token=settings.pie_trader_api_token
    )
    for tool_spec in build_pie_trader_tools(pie_trader_client):
        tool_registry.register(tool_spec)
    tool_executor = ToolExecutor(tool_registry)

    agent_registry = AgentRegistry()
    agent_registry.register(MarketIntelligenceAgent(tool_executor))
    return agent_registry, tool_registry, tool_executor


def create_app() -> FastAPI:
    app = FastAPI(
        title="PIE GenAI Platform",
        version=__version__,
        description="Agentic AI, RAG and Intelligence Platform for PIE Trader. "
        "See docs/architecture/SYSTEM_ARCHITECTURE.md for what is actually "
        "implemented versus planned.",
    )
    settings = get_settings()
    # One gateway/store/orchestrator/registry set per app instance, so
    # usage/audit tracking and conversation state (all in-memory, Stage
    # C/D/E) accumulate across requests instead of resetting on every call.
    app.state.llm_gateway = build_default_gateway(settings)
    app.state.conversation_store = ConversationStore()
    app.state.agent_registry, app.state.tool_registry, app.state.tool_executor = _build_agent_registry(
        settings
    )
    app.state.orchestrator = Orchestrator(
        app.state.conversation_store, app.state.llm_gateway, app.state.agent_registry
    )
    app.include_router(system_router)
    app.include_router(pie_trader_router)
    app.include_router(models_router)
    app.include_router(conversations_router)
    app.include_router(runs_router)
    app.include_router(agents_router)
    return app


app = create_app()
