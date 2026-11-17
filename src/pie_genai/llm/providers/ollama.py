"""Ollama provider — a real, working adapter for a self-hosted, open-weight
inference engine (your own infrastructure, not a third-party vendor API).
This is the platform's default model provider.

Unlike OwnGenAiProvider (still an unimplemented placeholder for a future
custom in-house model/service), this one makes a real HTTP call to a real
API: Ollama's POST /api/chat. It has not been exercised against a real,
running Ollama instance in this sandbox (no GPU/Ollama binary here) — see
tests/unit/test_ollama_provider.py for what *is* verified (the request
shape, response parsing, and error handling, all against a mocked HTTP
boundary), and docs/architecture/SYSTEM_ARCHITECTURE.md for the explicit
NOT VERIFIED note on a live round-trip.
"""

from __future__ import annotations

import httpx

from pie_genai.llm.providers.base import (
    ModelProvider,
    ModelProviderError,
    ModelRequest,
    ModelResponse,
)


class OllamaProvider(ModelProvider):
    provider_name = "Ollama (self-hosted, open-weight)"

    def __init__(self, base_url: str, default_model: str, timeout_s: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout_s = timeout_s

    def _messages(self, request: ModelRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        for turn in request.history:
            role = turn.get("role", "user")
            content = turn.get("content") or turn.get("text") or ""
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    async def invoke(self, request: ModelRequest) -> ModelResponse:
        model = request.model or self._default_model
        url = f"{self._base_url}/api/chat"
        payload = {"model": model, "messages": self._messages(request), "stream": False}
        timeout = min(request.timeout_s, self._timeout_s) if request.timeout_s else self._timeout_s

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.ConnectError as exc:
            raise ModelProviderError(
                f"Could not reach Ollama at {self._base_url} — is `ollama serve` running? "
                "(retryable: Ollama may just be starting up)",
                retryable=True,
            ) from exc
        except httpx.TimeoutException as exc:
            raise ModelProviderError(
                f"Ollama timed out after {timeout}s generating a response with model {model!r}",
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            # e.g. 404 = model not pulled — retrying the same request won't help.
            raise ModelProviderError(
                f"Ollama returned {exc.response.status_code} for model {model!r}: "
                f"{exc.response.text[:200]}",
                retryable=False,
            ) from exc
        except ValueError as exc:  # non-JSON body
            raise ModelProviderError(
                f"Ollama returned a non-JSON response from {url}", retryable=False
            ) from exc

        text = (body.get("message") or {}).get("content", "")
        # Ollama reports real token counts when available — prefer them
        # over the gateway's own rough estimate.
        prompt_tokens = body.get("prompt_eval_count")
        completion_tokens = body.get("eval_count")
        tokens = (
            prompt_tokens + completion_tokens
            if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int)
            else None
        )
        return ModelResponse(text=text, tokens=tokens)

    async def health(self) -> bool:
        """A real, cheap reachability check: GET /api/tags lists locally
        pulled models and has no side effects. True only if Ollama
        actually answers — never guessed."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
