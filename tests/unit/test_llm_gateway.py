import httpx
import pytest
import respx

from pie_genai.config import Settings
from pie_genai.llm.gateway import LlmGateway, build_default_gateway
from pie_genai.llm.providers.base import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)
from pie_genai.llm.registry import ModelRegistry, ModelSpec
from pie_genai.llm.router import TASK_SIMPLE_CONVERSATION, select_model
from pie_genai.llm.router import NoSuitableModelError


class _FlakyProvider(ModelProvider):
    """Test double only — fails `fail_times` times then succeeds. Used to
    prove the gateway's retry mechanics work, not to claim a second real
    model provider exists."""

    provider_name = "test-double-flaky"

    def __init__(self, fail_times: int, retryable: bool = True) -> None:
        self.calls = 0
        self._fail_times = fail_times
        self._retryable = retryable

    async def invoke(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise ModelProviderError("transient failure", retryable=self._retryable)
        return ModelResponse(text="ok", tokens=42)


def _registry_with(provider: ModelProvider, name: str = "test-model") -> ModelRegistry:
    return ModelRegistry(
        [ModelSpec(name=name, provider=provider, task_types=frozenset({TASK_SIMPLE_CONVERSATION}), context_window_tokens=0)]
    )


@pytest.mark.respx(base_url="http://localhost:11434")
async def test_default_gateway_fails_loudly_when_ollama_unreachable(respx_mock):
    # The default provider is now Ollama (see gateway.py's build_default_registry) —
    # a real adapter, not a skeleton. This sandbox has no Ollama running, so
    # the honest, real failure mode is a connection error, not a fabricated
    # response. Mocked with respx for determinism (a real Ollama install on
    # a dev machine must not make this test flaky).
    respx_mock.post("/api/chat").mock(side_effect=httpx.ConnectError("refused"))
    gateway = build_default_gateway(Settings())

    with pytest.raises(ModelProviderError) as exc_info:
        await gateway.execute(
            TASK_SIMPLE_CONVERSATION,
            ModelRequest(model="", system_instruction="", prompt="hello"),
        )

    assert exc_info.value.retryable is True  # Ollama starting up is worth a retry
    assert "Could not reach Ollama" in str(exc_info.value)
    # The failure is still recorded, not silently dropped.
    assert gateway.usage.all()[-1].success is False


@pytest.mark.respx(base_url="http://localhost:11434")
async def test_default_gateway_reports_missing_model_as_non_retryable(respx_mock):
    respx_mock.post("/api/chat").mock(
        return_value=httpx.Response(404, text="model 'llama3.1' not found")
    )
    settings = Settings()

    with pytest.raises(ModelProviderError) as exc_info:
        await build_default_gateway(settings).execute(
            TASK_SIMPLE_CONVERSATION,
            ModelRequest(model="", system_instruction="", prompt="hello"),
        )

    # A missing model can't be fixed by retrying the same request.
    assert exc_info.value.retryable is False
    assert "404" in str(exc_info.value)


async def test_retries_a_retryable_failure_then_succeeds():
    provider = _FlakyProvider(fail_times=1, retryable=True)
    gateway = LlmGateway(_registry_with(provider), max_attempts=2, retry_backoff_s=0.0)

    response = await gateway.execute(
        TASK_SIMPLE_CONVERSATION, ModelRequest(model="", system_instruction="", prompt="hi")
    )

    assert response.text == "ok"
    assert provider.calls == 2
    assert gateway.usage.all()[-1].success is True
    assert gateway.usage.all()[-1].tokens == 42


async def test_does_not_retry_a_non_retryable_failure():
    provider = _FlakyProvider(fail_times=5, retryable=False)
    gateway = LlmGateway(_registry_with(provider), max_attempts=3, retry_backoff_s=0.0)

    with pytest.raises(ModelProviderError):
        await gateway.execute(
            TASK_SIMPLE_CONVERSATION, ModelRequest(model="", system_instruction="", prompt="hi")
        )

    # Exactly one attempt — retrying a non-retryable error is pointless.
    assert provider.calls == 1


async def test_exhausts_retries_on_persistent_retryable_failure():
    provider = _FlakyProvider(fail_times=10, retryable=True)
    gateway = LlmGateway(_registry_with(provider), max_attempts=3, retry_backoff_s=0.0)

    with pytest.raises(ModelProviderError):
        await gateway.execute(
            TASK_SIMPLE_CONVERSATION, ModelRequest(model="", system_instruction="", prompt="hi")
        )

    assert provider.calls == 3
    assert gateway.usage.all()[-1].success is False
    assert gateway.usage.success_rate() == 0.0


def test_select_model_raises_for_unregistered_task_type():
    settings = Settings()
    gateway = build_default_gateway(settings)

    with pytest.raises(NoSuitableModelError):
        select_model(gateway.registry, "task_type_nobody_registered")
