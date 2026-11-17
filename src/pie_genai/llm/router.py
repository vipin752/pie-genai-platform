"""Task-based model selection — Section 7.1.

With only one model registered today, routing has nothing to choose
between; this module exists so that changes once a second model is added
are a registry entry, not a rewrite of every call site that currently
hardcodes a model name.
"""

from __future__ import annotations

from pie_genai.llm.registry import ModelRegistry, ModelSpec

# Subset of Section 7.1's task table. Extend as real task types are
# actually handled somewhere (an agent, a tool) — not speculatively.
TASK_SIMPLE_CONVERSATION = "simple_conversation"
TASK_COMPLEX_REASONING = "complex_reasoning"
TASK_STRUCTURED_EXTRACTION = "structured_extraction"


class NoSuitableModelError(RuntimeError):
    pass


def select_model(registry: ModelRegistry, task_type: str) -> ModelSpec:
    candidates = registry.for_task_type(task_type)
    if not candidates:
        raise NoSuitableModelError(
            f"No registered model declares task_type={task_type!r}. "
            f"Registered models: {[m.name for m in registry.list()]}"
        )
    # Tie-break rule once >1 candidate exists: prefer the larger context
    # window. A real scoring function (latency, cost, availability) is
    # Section 7.1's full requirement and is FUTURE PLAN until there is a
    # second model to actually choose between.
    return max(candidates, key=lambda m: m.context_window_tokens)
