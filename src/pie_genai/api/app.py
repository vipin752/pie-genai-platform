from __future__ import annotations

from fastapi import FastAPI

from pie_genai import __version__
from pie_genai.api.routes.models import router as models_router
from pie_genai.api.routes.pie_trader import router as pie_trader_router
from pie_genai.api.routes.system import router as system_router
from pie_genai.config import get_settings
from pie_genai.llm.gateway import build_default_gateway


def create_app() -> FastAPI:
    app = FastAPI(
        title="PIE GenAI Platform",
        version=__version__,
        description="Agentic AI, RAG and Intelligence Platform for PIE Trader. "
        "See docs/architecture/SYSTEM_ARCHITECTURE.md for what is actually "
        "implemented versus planned.",
    )
    # One gateway per app instance, so usage tracking (in-memory, Stage C)
    # accumulates across requests instead of resetting on every call.
    app.state.llm_gateway = build_default_gateway(get_settings())
    app.include_router(system_router)
    app.include_router(pie_trader_router)
    app.include_router(models_router)
    return app


app = create_app()
