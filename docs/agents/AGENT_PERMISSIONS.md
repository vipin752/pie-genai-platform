# Agent Permissions

Section 20's 5 levels, as actually implemented in
`src/pie_genai/tools/base.py`'s `PermissionLevel`:

| Level | Name | Used today? |
|---|---|---|
| 1 | READ | **Yes** — every tool and the one agent registered so far |
| 2 | RECOMMEND | Not used yet |
| 3 | CONFIGURE | Not used yet |
| 4 | SENSITIVE_CHANGE | Not used yet |
| 5 | FINANCIAL_ACTION | **Hard-rejected** at registration — see below |

## The one rule that's non-negotiable (master prompt Section 19)

GenAI must never submit a broker order, bypass PIE Trader's RiskManager,
or independently change trading/risk/capital state. This is enforced at
two independent points, not described once and trusted:

1. `ToolRegistry.register()` raises `FinancialActionToolRejectedError`
   for any `ToolSpec` with `permission_level is PermissionLevel.FINANCIAL_ACTION`.
   Tested: `tests/unit/test_tool_registry.py::test_registry_rejects_financial_action_tools`.
2. `PieTraderClient` (Stage G) simply has no method for the gateway's
   write endpoints (`/api/mode`, `/api/manual-trade`, `/api/squareoff`)
   — there's nothing to wrap even if someone tried.

## How tool access is actually checked

Not by permission level directly yet — by `ToolSpec.allowed_agents`, an
explicit per-tool allow-list checked in `ToolExecutor.execute()`. An
agent not in a tool's `allowed_agents` is denied, audited, and told why
(`reason_if_denied`). A permission-level-vs-agent-level comparison (e.g.
"this agent may only call tools at or below RECOMMEND") is FUTURE PLAN —
meaningless to build before a second permission level is actually used
by a real tool or agent.
