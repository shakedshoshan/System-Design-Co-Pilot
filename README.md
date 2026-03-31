# System Design Co-Pilot

Monorepo for an AI-guided system design assistant: **FastAPI** API (`apps/api`), **Next.js** UI (`apps/web`), **Kafka** worker (`apps/worker`), and **infra** tooling.

## Docs

- **Product and architecture:** [System_Design_CoPilot_Plan.md](./System_Design_CoPilot_Plan.md)
- **Build order (start here):** [Project_Execution_Guide.md](./Project_Execution_Guide.md)
- **What exists in the repo:** [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)

## Quick orientation

| Path | Role |
|------|------|
| `apps/api` | HTTP API, DB, LangGraph, LLM/RAG |
| `apps/web` | Next.js frontend |
| `apps/worker` | Kafka consumers |
| `infra/` | Dockerfiles, Kubernetes manifests |
| `packages/contracts` | Optional OpenAPI-generated types for the web app |

## Setup (Step 0)

1. **Python:** Use **3.12.x** (see `.python-version`). Create a venv and install the API when `pyproject.toml` lists dependencies (after Step 2).
2. **Node:** Use **20.x LTS** or newer (see `apps/web/package.json` → `engines` and `apps/web/.nvmrc`).
3. **Env:** Copy `.env.example` to `.env` at the repo root and fill in secrets (API keys) when you reach those steps.

## Local infra (Step 1)

Requires [Docker](https://docs.docker.com/get-docker/) (Docker Desktop on Windows) running.

```bash
docker compose up -d
```

- **PostgreSQL 16 + pgvector** — `localhost:5432`, user/db/password match `.env.example` (`app` / `system_design_copilot`).
- **Kafka (KRaft, Apache image)** — `localhost:9092` (same as `KAFKA_BOOTSTRAP_SERVERS` in `.env.example`).

Verify Postgres (after containers are healthy):

```bash
docker compose exec postgres psql -U app -d system_design_copilot -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Stop: `docker compose down` (add `-v` to remove data volumes).

Next: **Step 2** in [Project_Execution_Guide.md](./Project_Execution_Guide.md) — FastAPI skeleton.
