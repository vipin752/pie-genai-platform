import pytest

from pie_genai.config import Settings
from pie_genai.llm.gateway import build_default_gateway
from pie_genai.llm.providers.base import ModelProviderError, ModelRequest


@pytest.mark.asyncio
async def test_default_gateway_fails_loudly_when_unconfigured():
    settings = Settings(own_genai_endpoint=None, own_genai_api_key=None)
    gateway = build_default_gateway(settings)

    assert "Own GenAI" in gateway.provider_name

    with pytest.raises(ModelProviderError) as exc_info:
        await gateway.execute(
            ModelRequest(model="pie-genai-core", system_instruction="", prompt="hello")
        )

    assert exc_info.value.retryable is False
    assert "not configured yet" in str(exc_info.value)


@pytest.mark.asyncio
async def test_default_gateway_still_fails_once_endpoint_set_but_unimplemented():
    settings = Settings(own_genai_endpoint="https://example.invalid/genai", own_genai_api_key="x")
    gateway = build_default_gateway(settings)

    with pytest.raises(ModelProviderError) as exc_info:
        await gateway.execute(
            ModelRequest(model="pie-genai-core", system_instruction="", prompt="hello")
        )

    assert exc_info.value.retryable is False
    assert "not implemented yet" in str(exc_info.value)
