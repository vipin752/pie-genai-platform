# PIE GenAI Platform — System Architecture & Honest Status

This repository implements the master build prompt's **Stage A, Stage B,
Stage G** (read-only PIE Trader integration — see
[`docs/integration/PIE_TRADER_INTEGRATION.md`](../integration/PIE_TRADER_INTEGRATION.md)),
**Stage C** (model registry, task-based routing, retry/backoff, usage
tracking — one real provider only), **Stage D** (conversation/message/run
lifecycle, a heuristic intent classifier, a one-step planner, an
orchestrator), and **Stage E** (Tool Registry, Agent Registry, and one
real specialist agent — see
[`docs/agents/AGENT_CATALOG.md`](../agents/AGENT_CATALOG.md),
[`TOOL_CATALOG.md`](../agents/TOOL_CATALOG.md) and
[`AGENT_PERMISSIONS.md`](../agents/AGENT_PERMISSIONS.md)). Stages F, H, I,
J — RAG, memory, multimodal, workflows, frontend integration, evaluation,
production hardening — are **not implemented**. This document says so
plainly rather than describing them as if they existed, per the master
prompt's own rule: never claim a feature is production-ready merely
because its code exists, and never classify a feature's status beyond
the evidence.

Status labels below use the master prompt's own taxonomy (Section 6):
IMPLEMENTED, TESTED, PARTIALLY IMPLEMENTED, SCAFFOLD, DOCUMENTED ONLY,
FUTURE PLAN, BLOCKED, NOT VERIFIED.

## What exists today

| Capability | Status | Evidence |
|---|---|---|
| FastAPI application skeleton | IMPLEMENTED, TESTED | `src/pie_genai/api/app.py`, `tests/unit/test_system_routes.py` |
| Health / readiness / version / capabilities APIs | IMPLEMENTED, TESTED | `src/pie_genai/api/routes/system.py` — 4/4 covered by tests |
| Config loading (env-driven, no hardcoded secrets) | IMPLEMENTED, TESTED | `src/pie_genai/config.py` |
| Provider-neutral model interface (`ModelProvider`) | IMPLEMENTED | `src/pie_genai/llm/providers/base.py` — only one concrete provider exists so far, so "provider-neutral" is a contract, not yet proven by a second real implementation |
| Own-GenAI provider adapter | SCAFFOLD | `src/pie_genai/llm/providers/own_genai.py` — fails loudly by design; mirrors the same pattern already added on the pie-trader side (`ui/server/ai/llmGateway.ts`'s `OwnGenAiProviderAdapter`) for consistency across both repos |
| Model registry + task-based routing | IMPLEMENTED, TESTED | `src/pie_genai/llm/registry.py`, `router.py` — one model registered (`pie-genai-core`); the tie-break rule for >1 candidate is untested because there is no second model yet |
| Model gateway: retry (non-retryable errors skip retry), backoff, usage tracking | IMPLEMENTED, TESTED | `src/pie_genai/llm/gateway.py`, `usage.py` — retry/backoff proven against a test-double provider (`tests/unit/test_llm_gateway.py`), not against a second real model |
| Model gateway: streaming, circuit breaker, real multi-provider fallback, rate limiting | FUTURE PLAN | Section 7.2's full list — needs a second real provider to implement honestly |
| Model APIs (`/api/v1/models`, `/health`, `/usage`) | IMPLEMENTED, TESTED | `src/pie_genai/api/routes/models.py` — Section 14.4 |
| Conversation/message APIs (create/list/get/delete, list/submit messages) | IMPLEMENTED, TESTED | `src/pie_genai/api/routes/conversations.py` — Section 14.1. In-memory only (no DB); pagination not implemented |
| Run lifecycle APIs (get, cancel) | IMPLEMENTED, TESTED | `src/pie_genai/api/routes/runs.py` — Section 14.2 |
| Run event stream (`GET /runs/{id}/events`) | PARTIALLY IMPLEMENTED, TESTED | Replays a completed run's recorded events in Section 16's wire format; does **not** stream a still-running task live or support `Last-Event-ID` reconnect — today's one-step run finishes before a client could subscribe mid-flight. True live streaming is FUTURE PLAN until a real long-running step exists |
| Intent classification | SCAFFOLD, TESTED | `src/pie_genai/core/intent.py` — a keyword heuristic (confidence-capped at 0.85), not an ML/LLM classifier |
| Task planner | SCAFFOLD, TESTED | `src/pie_genai/core/planner.py` — always a single `call_model` step; Section 5.3's full plan shape (multi-step, parallel, approval-gated) needs Stage E to mean anything |
| Orchestrator | PARTIALLY IMPLEMENTED, TESTED | `src/pie_genai/core/orchestrator.py` — proves the full accepted→running→completed/failed/cancelled lifecycle against both a successful test-double model (`tests/unit/test_orchestrator.py`) and the real default (currently-failing) model. Cannot yet "coordinate specialist agents" (Section 5.1) — there are no agents (Stage E) |
| Cancellation | SCAFFOLD, TESTED | The mechanism (a flag the orchestrator checks once) is real and tested for the terminal-run-409 case; there is no long-running step yet for an in-flight cancel to actually interrupt |
| Tool Registry + permission enforcement + audit log | IMPLEMENTED, TESTED | `src/pie_genai/tools/` — `ToolRegistry.register()` hard-rejects `PermissionLevel.FINANCIAL_ACTION` in code (Section 19/26), not just by convention. See `docs/agents/TOOL_CATALOG.md` |
| Agent Registry + runtime | IMPLEMENTED, TESTED | `src/pie_genai/agents/` — one agent registered |
| Market Intelligence Agent (Section 6.3) | IMPLEMENTED, TESTED | `src/pie_genai/agents/market_intelligence_agent.py` — calls the real `trade_card`/`risk_state` tools and synthesizes a plain-text answer; proven against both a mocked successful gateway (real numbers in the answer) and an unreachable one (honest failure in the answer, never fabricated data). "Synthesis" is deterministic templating, not model-generated prose — see `docs/agents/AGENT_CATALOG.md` |
| Agent APIs (`/api/v1/agents`, `/{id}`, `/{id}/health`) | IMPLEMENTED, TESTED | `src/pie_genai/api/routes/agents.py` — Section 14.3 |
| Orchestrator routing a question to the agent vs. the model | IMPLEMENTED, TESTED | `core/planner.py` picks `call_agent` when the intent is `market_analysis` and the Market Intelligence Agent is registered, else falls back to `call_model` — real HTTP proof in `tests/unit/test_agents_routes.py` |
| Local dev Postgres/Redis (docker-compose) | SCAFFOLD | `docker-compose.yml` — nothing in the app connects to either yet |
| CI (pytest on push/PR) | IMPLEMENTED | `.github/workflows/ci.yml` |
| PIE Trader read-only integration (trade-card, dashboard, positions, risk) | IMPLEMENTED, TESTED (mocked contract) | `src/pie_genai/integrations/pie_trader/`, `src/pie_genai/api/routes/pie_trader.py` — see `docs/integration/PIE_TRADER_INTEGRATION.md` for exactly what's verified vs. not |

## What is explicitly not implemented (FUTURE PLAN)

Everything else in the master prompt, including but not limited to:

- Any specialist agent other than Market Intelligence (Section 6.1, 6.2,
  6.5–6.10 — Personal Assistant, Research, Strategy Research, Portfolio/
  Capital, Product Intelligence, Product Development, Data Analyst,
  Document Intelligence)
- RAG: ingestion, chunking, embeddings, retrieval, reranking, citations (Section 8)
- Memory service (Section 9)
- Multimodal adapters — image/audio/video (Section 10)
- Deep research workflows (Section 11)
- Durable workflow engine (Section 13)
- PIE Trader integration beyond the 4 read-only endpoints above (Section
  18) — nothing calls `analytics/` (Python) yet, and the gateway's write
  endpoints are intentionally never called (see
  `docs/integration/PIE_TRADER_INTEGRATION.md`'s scope boundary)
- Frontend/UI integration (Section 21) — `pie-trader/ui` is a separate
  repository and has not been wired to this one
- Evaluation framework, feedback APIs, product-intelligence persistence
  (Section 23–24)
- Any database schema or migration (Section 25) — `docker-compose.yml`
  starts Postgres/Redis containers; nothing in the app writes to them
- Security hardening beyond "no secrets in code/config defaults"
  (Section 26) — no auth, no RBAC, no rate limiting implemented yet
- Observability/OpenTelemetry (Section 27)

Do not infer any of the above exists because the master prompt describes
it. This table is the actual evidence.

## Architecture Decision — provider-neutral from the first line of code

Section 7 of the master prompt requires the platform never become
permanently dependent on one LLM provider. Rather than build a Gemini/
OpenAI-specific client first and "generalize later" (the trap most AI
wrapper projects fall into), the very first provider adapter is PIE
Trader's own in-house GenAI skeleton behind the `ModelProvider` interface
(`src/pie_genai/llm/providers/base.py`). A second, different provider
(commercial or self-hosted) can be added later as another class
implementing the same interface — `LlmGateway` and everything above it
never needs to change. This mirrors the identical decision already made on
the `pie-trader` repository's frontend (`ui/server/ai/llmGateway.ts`), so
both repositories share one mental model for "which AI provider answered
this."

## Recommended next iteration

With Stages A, B (foundation), C (model gateway), D (conversation/run
lifecycle), E (tools/agents) and G (read-only PIE Trader integration) now
in place, a market question gets a real, data-backed answer end to end —
proven by this session's own HTTP smoke test (`curl` a `banknifty`
question → `status: "completed"`, a real synthesized answer or an honest
"unavailable" if the gateway can't be reached — never a fabricated one).

The highest-leverage next step is now a **live round-trip**: boot a real
`backend/pietrader-gateway` (Postgres+Redis+Kafka) and re-run
`tests/unit/test_market_intelligence_agent.py`'s scenarios against it
instead of a mock, to retire the one "NOT VERIFIED" item Stage G left
open. After that, Stage F (RAG/memory) or a second specialist agent
(Section 6's Options Intelligence or Portfolio/Capital Agent, reusing the
same `dashboard`/`positions` tools already registered but unused) are
the natural next additions — either is additive to what exists, not a
rewrite.

Finishing Stage B's still-open items (structured logging, a standardized
Section 17 error envelope, a real OpenAPI contract file checked into
`contracts/openapi/` and validated in CI) remains worth doing before any
of this is exposed outside local development.
