"""Model gateway — the one place anything above this layer talks to an
LLM provider. Implements Section 7.2's retry, timeout and usage-tracking
requirements for a single configured model path. Model routing
(Section 7.1) picks which registered model serves a task; circuit
breakers, streaming and true multi-provider fallback (Section 7.2's full
list) are FUTURE PLAN until there is more than one working provider to
exercise them against honestly.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace

from pie_genai.config import Settings
from pie_genai.llm.providers.base import ModelProviderError, ModelRequest, ModelResponse
from pie_genai.llm.providers.own_genai import OwnGenAiProvider
from pie_genai.llm.registry import ModelRegistry, ModelSpec
from pie_genai.llm.router import (
    TASK_COMPLEX_REASONING,
    TASK_SIMPLE_CONVERSATION,
    TASK_STRUCTURED_EXTRACTION,
    select_model,
)
from pie_genai.llm.usage import UsageRecord, UsageTracker


def _estimate_tokens(request: ModelRequest, response: ModelResponse) -> int:
    return max(1, (len(request.system_instruction) + len(request.prompt) + len(response.text)) // 4)


class LlmGateway:
    def __init__(
        self,
        registry: ModelRegistry,
        usage: UsageTracker | None = None,
        max_attempts: int = 2,
        retry_backoff_s: float = 0.35,
    ) -> None:
        self._registry = registry
        self._usage = usage or UsageTracker()
        self._max_attempts = max_attempts
        self._retry_backoff_s = retry_backoff_s

    @property
    def registry(self) -> ModelRegistry:
        return self._registry

    @property
    def usage(self) -> UsageTracker:
        return self._usage

    async def execute(self, task_type: str, request: ModelRequest) -> ModelResponse:
        """Selects a model for `task_type`, invokes its provider with
        retry on retryable failures only (never retries a missing-config
        or not-implemented error — that can't be fixed by trying again),
        and records usage whether the call succeeds or exhausts retries.
        """
        model_spec: ModelSpec = select_model(self._registry, task_type)
        resolved_request = replace(request, model=model_spec.name)

        start = time.monotonic()
        last_error: ModelProviderError | None = None

        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await model_spec.provider.invoke(resolved_request)
                latency_ms = (time.monotonic() - start) * 1000
                tokens = response.tokens if response.tokens is not None else _estimate_tokens(
                    resolved_request, response
                )
                self._usage.record(
                    UsageRecord(
                        model=model_spec.name,
                        provider_name=model_spec.provider.provider_name,
                        success=True,
                        retryable_failure=False,
                        latency_ms=latency_ms,
                        tokens=tokens,
                    )
                )
                return response
            except ModelProviderError as exc:
                last_error = exc
                if not exc.retryable or attempt == self._max_attempts:
                    break
                await asyncio.sleep(self._retry_backoff_s * attempt)

        latency_ms = (time.monotonic() - start) * 1000
        self._usage.record(
            UsageRecord(
                model=model_spec.name,
                provider_name=model_spec.provider.provider_name,
                success=False,
                retryable_failure=bool(last_error and last_error.retryable),
                latency_ms=latency_ms,
                tokens=0,
            )
        )
        assert last_error is not None
        raise last_error


def build_default_registry(settings: Settings) -> ModelRegistry:
    """The one model registered today: PIE Trader's own GenAI skeleton.
    context_window_tokens is 0 (unknown) rather than a plausible-looking
    invented number — the real service doesn't exist yet to measure."""
    own_genai = OwnGenAiProvider(settings.own_genai_endpoint, settings.own_genai_api_key)
    return ModelRegistry(
        [
            ModelSpec(
                name="pie-genai-core",
                provider=own_genai,
                task_types=frozenset(
                    {TASK_SIMPLE_CONVERSATION, TASK_COMPLEX_REASONING, TASK_STRUCTURED_EXTRACTION}
                ),
                context_window_tokens=0,
                supports_structured_output=False,
                supports_streaming=False,
            )
        ]
    )


def build_default_gateway(settings: Settings) -> LlmGateway:
    return LlmGateway(build_default_registry(settings))
