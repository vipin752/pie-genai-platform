# PIE GenAI Platform

Open-source Agentic AI, RAG and Intelligence Platform for PIE Trader.

**Read [`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md)
first.** This is Stage A/B of a large, staged build — a FastAPI skeleton,
config loading, health/readiness/version APIs and a provider-neutral model
gateway with one (unimplemented) provider adapter. Conversations, agents,
RAG, memory, workflows and PIE Trader integration are not built yet; that
document says exactly what exists and what doesn't, with evidence.

This is a separate repository from
[`pie-trader`](https://github.com/vipin752/pie-trader) on purpose — see
Section 3 of the governing build prompt. GenAI will consume PIE Trader
capabilities through authenticated APIs once that integration exists; it
will never own trading, risk or capital logic, and PIE Trader remains the
sole source of truth for all of that.

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
