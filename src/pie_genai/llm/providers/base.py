"""Provider-neutral model interface.

Every LLM provider (own GenAI, a commercial vendor, a self-hosted model)
implements this same contract, so nothing above this layer (routing,
agents, orchestration — none of which exist yet; see
docs/architecture/SYSTEM_ARCHITECTURE.md) ever needs to know which
provider actually answered a request.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ModelRequest:
    model: str
    system_instruction: str
    prompt: str
    history: list[dict[str, str]] = field(default_factory=list)
    timeout_s: float = 30.0


@dataclass
class ModelResponse:
    text: str
    tokens: int | None = None


class ModelProviderError(RuntimeError):
    """Raised for any provider failure. `retryable=False` means retrying
    cannot help (missing config, not implemented) — callers should not
    spend a retry budget on it."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class ModelProvider(ABC):
    """Implemented by every concrete provider adapter."""

    provider_name: str

    @abstractmethod
    async def invoke(self, request: ModelRequest) -> ModelResponse:
        ...

    async def health(self) -> bool:
        """True if this provider is actually reachable right now. The
        default (no real check) assumes reachable — override with a real,
        cheap probe wherever one exists (see OllamaProvider.health())."""
        return True
