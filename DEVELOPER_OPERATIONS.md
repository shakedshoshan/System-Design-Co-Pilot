# Developer operations (cheat sheet)

More detail: [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md), [README.md](./README.md), [apps/api/app/kafka/KAFKA.md](./apps/api/app/kafka/KAFKA.md).

## Setup (repo root)

1. Copy `.env.example` → `.env`. Docker Postgres example: `postgresql+psycopg://app:app@localhost:5433/system_design_copilot`
2. `poetry install` (venv: `.venv/`)
3. `docker compose up -d` — Postgres **5433**, Kafka **9092**
4. `poetry run migrate upgrade head`
5. **Web UI (optional):** `cd apps/web && npm install`. Set `NEXT_PUBLIC_API_URL` in the **repo root** `.env` (same file as the API) or in `apps/web/.env.local`. Root `NEXT_PUBLIC_*` is merged in `apps/web/next.config.ts`. API **`CORS_ORIGINS`** must include the Next dev origin (`http://localhost:3000`, `http://127.0.0.1:3000` — see root `.env.example`).

## Commands

| What | Command |
|------|---------|
| API | `poetry run api` → http://127.0.0.1:8000 (`/docs`, `/health`, `/ready`) |
| Web (Next.js) | `cd apps/web && npm run dev` → http://localhost:3000 · prod build: `npm run build` then `npm run start` |
| Web lint | `cd apps/web && npm run lint` |
| Migrations | `poetry run migrate upgrade head` · new rev: `poetry run migrate revision --autogenerate -m "msg"` |
| Worker | `poetry run worker` |
| Tests | `poetry run pytest` (API under `apps/api/tests`) |

No Poetry: `pip install -e .` then `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir apps/api`

**Typical local UI path:** Docker (Postgres + Kafka if needed) → `poetry run api` → `cd apps/web && npm run dev`. With **`KAFKA_ASYNC_RUNS=true`**, also run **`poetry run worker`** so chat / architecture runs complete after HTTP **202**.

## Kafka (async runs)

Set `KAFKA_ENABLED=true`. For **202 + background jobs**: `KAFKA_ASYNC_RUNS=true`, then run **API + worker**; poll `GET /api/v1/sessions/{id}/messages`. Topic default: `architecture_copilot_events` (`KAFKA_TOPIC_EVENTS`). Event payloads: `apps/api/app/kafka/events/`.

## Postman

Workspace **`architecture-co-pilot`**, collection **Architecture Co-Pilot**, env **Architecture Co-Pilot — local** (`baseUrl` = `http://127.0.0.1:8000`). Imports: `architecture-co-pilot/postman/collections/*.json`.
