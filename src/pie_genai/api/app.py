from __future__ import annotations

from fastapi import FastAPI

from pie_genai import __version__
from pie_genai.api.routes.conversations import router as conversations_router
from pie_genai.api.routes.models import router as models_router
from pie_genai.api.routes.pie_trader import router as pie_trader_router
from pie_genai.api.routes.runs import router as runs_router
from pie_genai.api.routes.system import router as system_router
from pie_genai.config import get_settings
from pie_genai.conversations.store import ConversationStore
from pie_genai.core.orchestrator import Orchestrator
from pie_genai.llm.gateway import build_default_gateway


def create_app() -> FastAPI:
    app = FastAPI(
        title="PIE GenAI Platform",
        version=__version__,
        description="Agentic AI, RAG and Intelligence Platform for PIE Trader. "
        "See docs/architecture/SYSTEM_ARCHITECTURE.md for what is actually "
        "implemented versus planned.",
    )
    # One gateway/store/orchestrator per app instance, so usage tracking
    # and conversation state (both in-memory, Stage C/D) accumulate across
    # requests instead of resetting on every call.
    app.state.llm_gateway = build_default_gateway(get_settings())
    app.state.conversation_store = ConversationStore()
    app.state.orchestrator = Orchestrator(app.state.conversation_store, app.state.llm_gateway)
    app.include_router(system_router)
    app.include_router(pie_trader_router)
    app.include_router(models_router)
    app.include_router(conversations_router)
    app.include_router(runs_router)
    return app


app = create_app()
