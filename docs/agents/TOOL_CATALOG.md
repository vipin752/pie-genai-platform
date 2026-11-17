# Tool Catalog

4 tools registered; 2 are allowed for the one existing agent today. All 4
wrap Stage G's read-only `PieTraderClient` — see
[`../integration/PIE_TRADER_INTEGRATION.md`](../integration/PIE_TRADER_INTEGRATION.md)
for exactly what backend/pietrader-gateway endpoint each one calls and
what is/isn't verified about that call.

| ID | Name | Permission | Data classification | Timeout | Allowed agents |
|---|---|---|---|---|---|
| `pie_trader.trade_card` | Get Trade Card | READ | market-data | 5s | `market_intelligence_agent` |
| `pie_trader.dashboard` | Get Dashboard | READ | market-data | 5s | `market_intelligence_agent` |
| `pie_trader.positions` | Get Positions | READ | portfolio-read | 5s | `market_intelligence_agent` |
| `pie_trader.risk_state` | Get Risk State | READ | portfolio-read | 5s | `market_intelligence_agent` |

`dashboard` and `positions` are registered but not yet called by the one
existing agent (it only uses `trade_card` and `risk_state`) — registered
ahead of use is fine; a tool only an agent can reach once it's both
registered AND in that agent's `allowed_agents`, so this isn't a gap,
just unused capacity.

## Enforcement — two independent points, not one

1. `ToolRegistry.register()` hard-rejects anything with
   `permission_level == PermissionLevel.FINANCIAL_ACTION`
   (`FinancialActionToolRejectedError`) — see `src/pie_genai/tools/registry.py`.
2. `PieTraderClient` itself (Stage G) has no method for the gateway's
   write endpoints to wrap in the first place.

Both exist so that removing one doesn't silently remove the rule (master
prompt Section 26: security enforced in code, not only in a prompt or a
single check).

## Execution lifecycle (Section 12's diagram, as actually implemented)

`ToolExecutor.execute(tool_id, agent_id, **kwargs)`: look up the tool →
check `agent_id` is in `allowed_agents` → run the handler under
`timeout_s` → record a `ToolExecutionResult` to the in-memory audit log
either way (permitted-and-succeeded, permitted-and-failed, or denied) →
return it. Every call is audited; none of the three outcomes is dropped.

## Status

| Item | Status |
|---|---|
| Registry + permission enforcement + audit log | IMPLEMENTED, TESTED |
| The 4 PIE Trader tools | IMPLEMENTED, TESTED (mocked contract, same caveat as Stage G) |
| Input/output JSON Schema generation for each tool (vs. the Python-level `handler` signature today) | FUTURE PLAN |
| Idempotency keys, rate limiting per tool | FUTURE PLAN — every tool today is a plain read; nothing has needed either yet |
