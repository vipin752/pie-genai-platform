# PIE Trader Integration (Stage G)

Read-only integration with `backend/pietrader-gateway`'s real, already-tested
REST contract. No write/execution endpoint is wired, by design — see
"Scope boundary" below.

## What's wired

| Method | pie-genai-platform endpoint | pie-trader gateway endpoint | DTO |
|---|---|---|---|
| GET | `/api/v1/integrations/pie-trader/health` | `/actuator/health` | — |
| GET | `/api/v1/integrations/pie-trader/trade-card?symbol=` | `/api/trade-card?symbol=` | `TradeCard` |
| GET | `/api/v1/integrations/pie-trader/dashboard` | `/api/dashboard` | `Dashboard` |
| GET | `/api/v1/integrations/pie-trader/positions` | `/api/positions` | `Position[]` |
| GET | `/api/v1/integrations/pie-trader/risk` | `/api/risk` | `RiskStateEntry[]` |

DTOs (`src/pie_genai/integrations/pie_trader/dto.py`) mirror the gateway's
real JSON field-for-field — copied from `com.pietrader.mapper.TradeCardMapper`
and `com.pietrader.controller.DashboardController` in the `pie-trader`
repository, not invented. `session`, `expiry`, `signals`, `fear_index`,
`trading_card` and `execution_plan` inside `TradeCard` are passed through
as plain dicts rather than fully typed — this adapter has verified the
top-level shape and `option`/`risk`/`levels`/`execution` exactly, not
those four builders' internals yet.

Every successful response carries a `DataProvenance` (instrument, source,
fetched-at timestamp, live/unavailable status) per master prompt §18.
Nothing here silently returns stale or fabricated data: an unreachable or
malformed response raises `PieTraderIntegrationError`, which the API
layer maps to HTTP 503.

## Scope boundary — read-only is not a placeholder

`PieTraderClient` has no method for the gateway's write endpoints
(`POST /api/mode`, `/api/manual-trade`, `/api/squareoff`). This is the
master prompt's own absolute rule (§19): GenAI must never submit a
broker order, bypass the Risk Manager, or independently change trading
state. If/when a controlled "propose an action, require explicit human +
RiskManager approval" workflow is designed, it is new work with its own
review — not an extra method quietly added to this client.

## Status

| Item | Status |
|---|---|
| Client + DTOs + routes | IMPLEMENTED |
| Mocked-contract tests (respx, response shapes copied from the real gateway code) | TESTED — 12 tests in `tests/unit/test_pie_trader_client.py` and `test_pie_trader_routes.py` |
| Live round-trip against a running `backend/pietrader-gateway` | **NOT VERIFIED** — this session did not boot the gateway (it needs Postgres/Redis/Kafka and Flyway migrations); the contract is grounded in reading that repository's source and its own passing test suite, not in a live call made from here |
| Auth header | Sends `Authorization: Bearer <PIE_TRADER_API_TOKEN>` if configured, but the gateway has no real auth yet (`SecurityConfig` permits all) — nothing to verify against until that lands |
| Options/portfolio/capital "intelligence tools" the master prompt describes (§6.4, §6.6) as agent-facing tools | **FUTURE PLAN** — this is the HTTP adapter layer only; wrapping these calls as registered, permissioned Tool objects is Stage E (Tool Registry), not done here |
