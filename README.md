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
| `architecture-co-pilot/` | Postman collection exports + API workspace notes |
| `apps/api/app/routers/architecture_copilot` | Product routes under `/api/v1` (see `.cursor/skills/architecture-co-pilot-api`) |

## Setup (Step 0)

1. **Python:** Use **3.12.x** (see `.python-version`).
2. **Node:** Use **20.x LTS** or newer (see `apps/web/package.json` → `engines` and `apps/web/.nvmrc`).
3. **Env:** Copy `.env.example` to `.env` at the repo root and fill in secrets (API keys) when you reach those steps.

### Poetry (recommended — venv at repo root)

From the **repository root** (requires [Poetry](https://python-poetry.org/docs/#installation) and Python **3.11+** on your PATH; **3.12.x** is still recommended — see `.python-version`):

```powershell
cd "path\to\System Design Co-Pilot"
poetry env use python
poetry install
poetry run api
```

`poetry env use python` binds the venv to whatever `python` is first on your PATH (e.g. 3.11.3). With **3.12** installed you can use `poetry env use 3.12` instead.

- **`poetry.toml`** sets **`in-project = true`**, so the environment lives in **`.venv/`** at the repo root.
- **`poetry run api`** runs FastAPI with reload (see **`devtools/run_api.py`** and `[tool.poetry.scripts]` in root **`pyproject.toml`**).
- The API package is pulled in as a path dependency from **`apps/api`** (editable).

If Poetry picks the wrong interpreter, set it explicitly, e.g. `poetry env use "C:\Path\To\python.exe"`, then `poetry install`.

### pip / venv (without Poetry)

Create a venv under `apps/api` and `pip install -e .` as in **API (Step 2)** below.

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

## API (Step 2)

From the repo root, ensure `.env` exists (copy from `.env.example`). Settings load from the **repo root** `.env` first, then `apps/api/.env` if present.

**With Poetry (from repo root):** `poetry run api` (after `poetry install`). Same as the Poetry section above.

**With pip (from `apps/api`):**

```bash
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **GET** [`/health`](http://127.0.0.1:8000/health) — process liveness.
- **GET** [`/ready`](http://127.0.0.1:8000/ready) — checks PostgreSQL using `DATABASE_URL` (503 if unset or DB unreachable). Run Docker Compose (Step 1) for a successful ready check.
- **OpenAPI** — [`/docs`](http://127.0.0.1:8000/docs)

**API contract:** Successful JSON responses use `{ "data": { ... }, "meta": { "request_id", "timestamp" } }`. Errors use `{ "error": { "code", "message", "details?" }, "meta": ... }`. Send optional header `X-Request-ID` (or reuse the one returned) to correlate logs in `apps/api/logs/app.log` (rotating JSON; see `.env.example` for `LOG_*`).

`API_HOST` / `API_PORT` in `.env` are documented for later process managers; the command above uses uvicorn flags directly.

Next: **Step 3** in [Project_Execution_Guide.md](./Project_Execution_Guide.md) — database schema and Alembic.
