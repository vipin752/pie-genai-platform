"""Agent model — Section 5.4.

An Agent is a registered spec plus a runnable. Section 5.4's full list
(model requirements, retry policy, evaluation profile) is trimmed to
what MarketIntelligenceAgent actually uses - fields nothing reads yet
are not added speculatively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pie_genai.tools.base import PermissionLevel, ToolExecutionResult


@dataclass
class AgentResult:
    text: str
    tool_calls: list[ToolExecutionResult] = field(default_factory=list)


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    description: str
    domain: str
    version: str
    capabilities: tuple[str, ...]
    tools_allowed: frozenset[str]
    permission_level: PermissionLevel
    timeout_s: float
    status: str = "available"


class Agent(Protocol):
    spec: AgentSpec

    async def run(self, user_text: str) -> AgentResult: ...
