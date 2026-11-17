from __future__ import annotations

from fastapi import FastAPI

from pie_genai import __version__
from pie_genai.api.routes.system import router as system_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="PIE GenAI Platform",
        version=__version__,
        description="Agentic AI, RAG and Intelligence Platform for PIE Trader. "
        "See docs/architecture/SYSTEM_ARCHITECTURE.md for what is actually "
        "implemented versus planned.",
    )
    app.include_router(system_router)
    return app


app = create_app()
