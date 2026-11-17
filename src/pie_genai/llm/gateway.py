"""Model gateway — the one place anything above this layer talks to an
LLM provider. Section 7 of the master prompt describes the full
production shape (routing, retries, circuit breakers, usage tracking,
streaming); this is the Stage C starting point only: a single configured
provider, invoked directly, with no retry/fallback/routing logic yet.
"""

from __future__ import annotations

from pie_genai.config import Settings
from pie_genai.llm.providers.base import ModelProvider, ModelRequest, ModelResponse
from pie_genai.llm.providers.own_genai import OwnGenAiProvider


class LlmGateway:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    async def execute(self, request: ModelRequest) -> ModelResponse:
        return await self._provider.invoke(request)


def build_default_gateway(settings: Settings) -> LlmGateway:
    """The default gateway: PIE Trader's own GenAI provider skeleton."""
    return LlmGateway(OwnGenAiProvider(settings.own_genai_endpoint, settings.own_genai_api_key))
