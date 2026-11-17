# PIE GenAI Platform

Open-source Agentic AI, RAG and Intelligence Platform for PIE Trader.

**Read [`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md)
first.** Stages A, B (foundation), C (model gateway — Ollama, self-hosted,
is the real default provider), D (conversation/run lifecycle), E
(tools/agents) and G (read-only PIE Trader integration) are built and
tested. RAG, memory, multimodal and the durable workflow engine are not;
that document says exactly what exists and what doesn't, with evidence.

This is a separate repository from
[`pie-trader`](https://github.com/vipin752/pie-trader) on purpose — see
Section 3 of the governing build prompt. GenAI consumes PIE Trader's
read-only capabilities (trade-card, dashboard, positions, risk) through
`src/pie_genai/integrations/pie_trader/`; it never owns trading, risk or
capital logic, and PIE Trader remains the sole source of truth for all
of that. For running this alongside the full PIE Trader stack (gateway,
`ui/`, Keycloak), see `pie-trader`'s
[`docs/LOCAL_SETUP.md`](https://github.com/vipin752/pie-trader/blob/development/docs/LOCAL_SETUP.md).

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # all blank by default - see SYSTEM_ARCHITECTURE.md
pytest -v
uvicorn pie_genai.api.app:app --reload
```

Then: `curl localhost:8000/api/v1/health`.

## Local Postgres/Redis (not yet used by the app)

```bash
cp .env.example .env   # fill in a real POSTGRES_PASSWORD
docker compose up -d
```
