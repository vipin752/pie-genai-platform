# PIE GenAI Platform — System Architecture & Honest Status

This repository implements the master build prompt's **Stage A and Stage B**,
and the very start of **Stage C** (one provider adapter, no routing yet).
Stages D through J — conversation/orchestration, agents, RAG, memory,
multimodal, workflows, PIE Trader integration, frontend integration,
evaluation, production hardening — are **not implemented**. This document
says so plainly rather than describing them as if they existed, per the
master prompt's own rule: never claim a feature is production-ready merely
because its code exists, and never classify a feature's status beyond the
evidence.

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
| Model gateway (single provider, no routing/retry/fallback/streaming) | PARTIALLY IMPLEMENTED | `src/pie_genai/llm/gateway.py` — Section 7's full model router, circuit breaker, usage tracking and streaming are FUTURE PLAN |
| Local dev Postgres/Redis (docker-compose) | SCAFFOLD | `docker-compose.yml` — nothing in the app connects to either yet |
| CI (pytest on push/PR) | IMPLEMENTED | `.github/workflows/ci.yml` |

## What is explicitly not implemented (FUTURE PLAN)

Everything else in the master prompt, including but not limited to:

- Conversation/message/run APIs and lifecycle (Section 14.1–14.2)
- AI Orchestrator, Intent Classifier, Task Planner (Section 5)
- Agent registry and runtime, any specialist agent (Section 5.4, Section 6)
- Tool registry and tool execution policy engine (Section 12)
- RAG: ingestion, chunking, embeddings, retrieval, reranking, citations (Section 8)
- Memory service (Section 9)
- Multimodal adapters — image/audio/video (Section 10)
- Deep research workflows (Section 11)
- Durable workflow engine (Section 13)
- PIE Trader integration adapters of any kind (Section 18) — this repo
  does not call `backend/pietrader-gateway` or `analytics/` yet
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

Per the master prompt's own staged delivery sequence (Section 32), the
smallest valuable next step is finishing **Stage B** (structured logging,
error-handling middleware, a real OpenAPI contract file checked into
`contracts/openapi/` and validated in CI) before starting **Stage D**
(conversation APIs) — building conversation/run endpoints before the
foundation they sit on is solid would mean redoing them once logging,
error contracts and auth land.
