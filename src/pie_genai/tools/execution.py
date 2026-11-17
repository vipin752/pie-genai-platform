"""Tool execution — Section 12's lifecycle diagram, minus the plan/agent-
selection steps (those live in core/orchestrator.py and agents/):
permission check -> execute -> record result. Every call is audited,
whether permitted, denied, or failed - "audit_policy: always" on every
ToolSpec is not optional here.
"""

from __future__ import annotations

import asyncio
import time

from pie_genai.tools.base import ToolExecutionResult
from pie_genai.tools.registry import ToolRegistry


class ToolAuditLog:
    """In-memory only - see docs/architecture/SYSTEM_ARCHITECTURE.md's
    persistence note. Every ToolExecutionResult lands here, including
    denied and failed calls, never just successes."""

    def __init__(self) -> None:
        self._records: list[ToolExecutionResult] = []

    def record(self, result: ToolExecutionResult) -> None:
        self._records.append(result)

    def all(self) -> list[ToolExecutionResult]:
        return list(self._records)

    def for_tool(self, tool_id: str) -> list[ToolExecutionResult]:
        return [r for r in self._records if r.tool_id == tool_id]


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, audit_log: ToolAuditLog | None = None) -> None:
        self._registry = registry
        self._audit = audit_log or ToolAuditLog()

    @property
    def audit_log(self) -> ToolAuditLog:
        return self._audit

    async def execute(self, tool_id: str, agent_id: str, **kwargs) -> ToolExecutionResult:
        spec = self._registry.get(tool_id)
        if spec is None:
            result = ToolExecutionResult(
                tool_id=tool_id,
                agent_id=agent_id,
                permitted=False,
                success=False,
                output=None,
                error=None,
                duration_ms=0.0,
                reason_if_denied=f"tool {tool_id!r} is not registered",
            )
            self._audit.record(result)
            return result

        if agent_id not in spec.allowed_agents:
            result = ToolExecutionResult(
                tool_id=tool_id,
                agent_id=agent_id,
                permitted=False,
                success=False,
                output=None,
                error=None,
                duration_ms=0.0,
                reason_if_denied=f"agent {agent_id!r} is not in tool {tool_id!r}'s allowed_agents",
            )
            self._audit.record(result)
            return result

        start = time.monotonic()
        try:
            output = await asyncio.wait_for(spec.handler(**kwargs), timeout=spec.timeout_s)
            result = ToolExecutionResult(
                tool_id=tool_id,
                agent_id=agent_id,
                permitted=True,
                success=True,
                output=output,
                error=None,
                duration_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as exc:  # noqa: BLE001 - any handler failure is a tool failure, recorded honestly
            result = ToolExecutionResult(
                tool_id=tool_id,
                agent_id=agent_id,
                permitted=True,
                success=False,
                output=None,
                error=str(exc),
                duration_ms=(time.monotonic() - start) * 1000,
            )
        self._audit.record(result)
        return result
