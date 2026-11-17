"""Task planner — Section 5.3.

SCAFFOLD: produces a single-step plan (call the model gateway with a task
type). Section 5.3's full plan shape (required agents/tools, parallel
steps, approval requirements, timeout/retry policy per step) is FUTURE
PLAN until Stage E (agents/tools) exists for a plan to actually need more
than one step.
"""

from __future__ import annotations

from dataclasses import dataclass

from pie_genai.core.intent import INTENT_MARKET_ANALYSIS, IntentResult
from pie_genai.llm.router import TASK_COMPLEX_REASONING, TASK_SIMPLE_CONVERSATION


@dataclass
class PlanStep:
    kind: str  # only "call_model" exists today
    task_type: str


@dataclass
class Plan:
    steps: list[PlanStep]


def build_plan(intent_result: IntentResult) -> Plan:
    task_type = (
        TASK_COMPLEX_REASONING if intent_result.intent == INTENT_MARKET_ANALYSIS else TASK_SIMPLE_CONVERSATION
    )
    return Plan(steps=[PlanStep(kind="call_model", task_type=task_type)])
