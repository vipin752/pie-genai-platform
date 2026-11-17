"""Tool model — Section 12.

A Tool is how an agent touches the real world. Every field the master
prompt requires is here except two that genuinely need more than one
tool to mean anything yet (retry policy, idempotency requirements —
every tool registered so far is a plain read, so "retry" and "idempotent"
are trivially true and not worth a field until a write tool exists to
need them for real).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Awaitable, Callable


class PermissionLevel(IntEnum):
    """Section 20's 5 levels, in ascending sensitivity."""

    READ = 1
    RECOMMEND = 2
    CONFIGURE = 3
    SENSITIVE_CHANGE = 4
    FINANCIAL_ACTION = 5


@dataclass(frozen=True)
class ToolSpec:
    id: str
    name: str
    description: str
    version: str
    permission_level: PermissionLevel
    data_classification: str  # e.g. "market-data", "portfolio-read"
    timeout_s: float
    allowed_agents: frozenset[str]
    handler: Callable[..., Awaitable[Any]]
    audit_policy: str = "always"  # every call is audited; no tool opts out


@dataclass
class ToolExecutionResult:
    tool_id: str
    agent_id: str
    permitted: bool
    success: bool
    output: Any | None
    error: str | None
    duration_ms: float
    reason_if_denied: str | None = None
