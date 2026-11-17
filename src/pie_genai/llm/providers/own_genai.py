"""SKELETON — PIE Trader's own GenAI model/service.

Mirrors the same OwnGenAiProviderAdapter pattern already added on the
pie-trader side (ui/server/ai/llmGateway.ts): the platform's default
provider is PIE Trader's own model/service, not a third-party vendor.

NOT YET IMPLEMENTED. It fails loudly instead of fabricating a response,
per this project's own rule against presenting invented data as fact.
Intended contract once built: a plain HTTP POST to OWN_GENAI_ENDPOINT
with {model, system_instruction, prompt, history}, bearer-authenticated
via OWN_GENAI_API_KEY, returning {text, tokens}.
"""

from __future__ import annotations

from pie_genai.llm.providers.base import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)


class OwnGenAiProvider(ModelProvider):
    provider_name = "PIE Trader Own GenAI (skeleton — not yet implemented)"

    def __init__(self, endpoint: str | None, api_key: str | None) -> None:
        self._endpoint = endpoint
        self._api_key = api_key

    async def invoke(self, request: ModelRequest) -> ModelResponse:
        if not self._endpoint:
            raise ModelProviderError(
                "Own GenAI provider is a skeleton only — OWN_GENAI_ENDPOINT is "
                "not configured yet. Set OWN_GENAI_ENDPOINT/OWN_GENAI_API_KEY "
                "once the in-house model/service exists.",
                retryable=False,
            )
        # TODO(own-genai): implement the real HTTP call once OWN_GENAI_ENDPOINT
        # points at a live service. Left unimplemented on purpose — this is a
        # template for that future work.
        raise ModelProviderError(
            "Own GenAI provider endpoint is configured but the client is not "
            "implemented yet.",
            retryable=False,
        )
