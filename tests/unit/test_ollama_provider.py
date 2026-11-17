"""Tests OllamaProvider against Ollama's real, documented /api/chat
contract (mocked via respx — no real Ollama instance in this sandbox).
A live round-trip against a real running Ollama is NOT VERIFIED here;
see docs/architecture/SYSTEM_ARCHITECTURE.md.
"""

import httpx
import pytest

from pie_genai.llm.providers.base import ModelProviderError, ModelRequest
from pie_genai.llm.providers.ollama import OllamaProvider

BASE_URL = "http://localhost:11434"


@pytest.mark.respx(base_url=BASE_URL)
async def test_invoke_sends_system_history_and_prompt_as_messages(respx_mock):
    route = respx_mock.post("/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "llama3.1",
                "message": {"role": "assistant", "content": "hello back"},
                "done": True,
                "prompt_eval_count": 12,
                "eval_count": 5,
            },
        )
    )
    provider = OllamaProvider(BASE_URL, default_model="llama3.1")

    response = await provider.invoke(
        ModelRequest(
            model="",
            system_instruction="Be concise.",
            prompt="hi there",
            history=[{"role": "user", "content": "earlier turn"}],
        )
    )

    assert response.text == "hello back"
    assert response.tokens == 17  # 12 + 5, Ollama's real counts, not an estimate

    sent = route.calls[0].request
    import json

    body = json.loads(sent.content)
    assert body["model"] == "llama3.1"
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "earlier turn"},
        {"role": "user", "content": "hi there"},
    ]


@pytest.mark.respx(base_url=BASE_URL)
async def test_invoke_uses_request_model_override_when_given(respx_mock):
    respx_mock.post("/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "ok"}})
    )
    provider = OllamaProvider(BASE_URL, default_model="llama3.1")

    await provider.invoke(ModelRequest(model="qwen2.5:14b", system_instruction="", prompt="hi"))

    sent_body = __import__("json").loads(
        respx_mock.calls.last.request.content
    )
    assert sent_body["model"] == "qwen2.5:14b"


@pytest.mark.respx(base_url=BASE_URL)
async def test_connect_error_is_retryable(respx_mock):
    respx_mock.post("/api/chat").mock(side_effect=httpx.ConnectError("refused"))
    provider = OllamaProvider(BASE_URL, default_model="llama3.1")

    with pytest.raises(ModelProviderError) as exc_info:
        await provider.invoke(ModelRequest(model="", system_instruction="", prompt="hi"))

    assert exc_info.value.retryable is True
    assert "ollama serve" in str(exc_info.value)


@pytest.mark.respx(base_url=BASE_URL)
async def test_timeout_is_retryable(respx_mock):
    respx_mock.post("/api/chat").mock(side_effect=httpx.TimeoutException("too slow"))
    provider = OllamaProvider(BASE_URL, default_model="llama3.1")

    with pytest.raises(ModelProviderError) as exc_info:
        await provider.invoke(ModelRequest(model="", system_instruction="", prompt="hi"))

    assert exc_info.value.retryable is True


@pytest.mark.respx(base_url=BASE_URL)
async def test_404_missing_model_is_not_retryable(respx_mock):
    respx_mock.post("/api/chat").mock(
        return_value=httpx.Response(404, text="model \"nope\" not found")
    )
    provider = OllamaProvider(BASE_URL, default_model="nope")

    with pytest.raises(ModelProviderError) as exc_info:
        await provider.invoke(ModelRequest(model="", system_instruction="", prompt="hi"))

    assert exc_info.value.retryable is False
    assert "404" in str(exc_info.value)


@pytest.mark.respx(base_url=BASE_URL)
async def test_missing_token_counts_fall_back_to_none(respx_mock):
    # Older/customized Ollama builds may omit the count fields.
    respx_mock.post("/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "hi"}})
    )
    provider = OllamaProvider(BASE_URL, default_model="llama3.1")

    response = await provider.invoke(ModelRequest(model="", system_instruction="", prompt="hi"))

    assert response.tokens is None
