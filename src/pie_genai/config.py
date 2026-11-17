"""Application configuration.

Values come from environment variables (see .env.example). No secret ever
has a real default here — an unset value stays empty/None, and code that
needs it (e.g. the LLM gateway) fails loudly rather than silently using a
placeholder.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "pie-genai-platform"
    app_env: str = "development"
    log_level: str = "INFO"

    # Own GenAI provider (server/ai equivalent on the pie-trader side uses
    # the same OwnGenAiProvider pattern — see llm/providers/own_genai.py).
    # Kept as a placeholder for a future custom in-house model/service,
    # distinct from choosing a specific self-hosted inference engine below.
    own_genai_endpoint: str | None = None
    own_genai_api_key: str | None = None

    # Ollama — a real, self-hosted inference engine (your own
    # infrastructure, not a third-party vendor API) and this platform's
    # default model provider. No API key: Ollama has none by default.
    # See llm/providers/ollama.py.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout_s: float = 60.0

    # Persistence — not wired to a real database yet (see
    # docs/architecture/SYSTEM_ARCHITECTURE.md, Stage B status). Present so
    # config loading and docker-compose agree on the same variable names
    # once persistence is actually implemented.
    database_url: str | None = None
    redis_url: str | None = None

    # PIE Trader integration (Section 18 of the master prompt) — not wired
    # yet. Read-only once implemented; never a competing source of truth.
    pie_trader_gateway_url: str = "http://localhost:8080"
    pie_trader_api_token: str | None = None


def get_settings() -> Settings:
    return Settings()
