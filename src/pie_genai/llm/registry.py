"""Model registry — Section 7.2's "model registry" and "model configuration"
requirements. Holds what models exist and which provider serves each one,
so routing (router.py) and the gateway never hardcode a model name.

Only one entry exists today: PIE Trader's own GenAI skeleton. The registry
mechanism supports more, but adding a second provider here would be
fabricating a capability this platform doesn't have — see
docs/architecture/SYSTEM_ARCHITECTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from pie_genai.llm.providers.base import ModelProvider


@dataclass(frozen=True)
class ModelSpec:
    name: str
    provider: ModelProvider
    task_types: frozenset[str]
    context_window_tokens: int
    supports_structured_output: bool = False
    supports_streaming: bool = False


class ModelRegistry:
    def __init__(self, models: list[ModelSpec]) -> None:
        if not models:
            raise ValueError("ModelRegistry needs at least one ModelSpec")
        self._models: dict[str, ModelSpec] = {m.name: m for m in models}

    def get(self, name: str) -> ModelSpec | None:
        return self._models.get(name)

    def list(self) -> list[ModelSpec]:
        return list(self._models.values())

    def for_task_type(self, task_type: str) -> list[ModelSpec]:
        return [m for m in self._models.values() if task_type in m.task_types]
