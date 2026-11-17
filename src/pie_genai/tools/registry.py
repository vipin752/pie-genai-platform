"""Tool registry — Section 12.

register() is where Section 19's absolute rule is enforced in code, not
just in a prompt (Section 26: "Do not rely only on prompt instructions
for security"): nothing with permission_level FINANCIAL_ACTION can ever
be registered here. If a future financial-action tool is genuinely
needed, it is new, separately reviewed work with its own enforcement
path through PIE Trader's real RiskManager - never a flag flipped on
this registry.
"""

from __future__ import annotations

from pie_genai.tools.base import PermissionLevel, ToolSpec


class FinancialActionToolRejectedError(ValueError):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.permission_level is PermissionLevel.FINANCIAL_ACTION:
            raise FinancialActionToolRejectedError(
                f"Tool {spec.id!r} declares permission_level=FINANCIAL_ACTION. "
                "This platform never registers a tool that can place, modify or "
                "cancel an order, or otherwise take a financial action - that "
                "authority belongs exclusively to PIE Trader's RiskManager "
                "(master prompt Section 19). This is a hard rejection, not a "
                "policy to configure around."
            )
        self._tools[spec.id] = spec

    def get(self, tool_id: str) -> ToolSpec | None:
        return self._tools.get(tool_id)

    def list(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def for_agent(self, agent_id: str) -> list[ToolSpec]:
        return [t for t in self._tools.values() if agent_id in t.allowed_agents]
