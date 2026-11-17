"""Task planner — Section 5.3.

SCAFFOLD: produces a single-step plan - "call_agent" when a registered
agent actually declares market-analysis capability, otherwise
"call_model". Section 5.3's full plan shape (parallel steps, approval
requirements, per-step timeout/retry policy) is FUTURE PLAN until a
real multi-step need exists - a plan with one step doesn't need it yet.
"""

from __future__ import annotations

from dataclasses import dataclass

from pie_genai.core.intent import INTENT_MARKET_ANALYSIS, IntentResult
from pie_genai.llm.router import TASK_COMPLEX_REASONING, TASK_SIMPLE_CONVERSATION

# The one agent this planner currently knows how to route to. Kept as a
# plain string rather than importing agents/market_intelligence_agent.py,
# so core/ (orchestration) does not depend on a specific agent's module -
# only on whether that agent's id is present in the available set the
# caller passes in.
MARKET_INTELLIGENCE_AGENT_ID = "market_intelligence_agent"


@dataclass
class PlanStep:
    kind: str  # "call_model" | "call_agent"
    task_type: str | None = None
    agent_id: str | None = None


@dataclass
class Plan:
    steps: list[PlanStep]


def build_plan(intent_result: IntentResult, available_agent_ids: frozenset[str] = frozenset()) -> Plan:
    if intent_result.intent == INTENT_MARKET_ANALYSIS and MARKET_INTELLIGENCE_AGENT_ID in available_agent_ids:
        return Plan(steps=[PlanStep(kind="call_agent", agent_id=MARKET_INTELLIGENCE_AGENT_ID)])

    task_type = (
        TASK_COMPLEX_REASONING if intent_result.intent == INTENT_MARKET_ANALYSIS else TASK_SIMPLE_CONVERSATION
    )
    return Plan(steps=[PlanStep(kind="call_model", task_type=task_type)])
