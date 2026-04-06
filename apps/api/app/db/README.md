# Database (`app/db`)

SQLAlchemy models, session factory, and how to run migrations.

## Layout

| Item | Role |
|------|------|
| `base.py` | `DeclarativeBase` for ORM models |
| `models/__init__.py` | `DesignSession`, `Message`, `Artifact`, `EventLog`, `ProcessedKafkaEvent` |
| `session.py` | `get_engine()`, `get_db()` (FastAPI), `session_factory()` |
| `schema.sql` | Plain SQL snapshot of the **initial** core tables (for reading / diffs / pgAdmin). |

**Applied schema** in real environments = **Alembic** under `apps/api/migrations/versions/`. Keep `schema.sql` aligned when you add migrations (or treat the latest revision as the detailed truth). The folder is named `migrations` (not `alembic`) so `apps/api` on `PYTHONPATH` never shadows the PyPI `alembic` package.

## Postgres in dev (Docker)

1. Docker Desktop running → repo root: `.\scripts\docker_up_postgres.ps1` (or `docker compose up -d postgres`).
2. **`.env`:** `DATABASE_URL=postgresql+psycopg://app:app@localhost:5433/system_design_copilot` (host **5433** maps to container 5432; avoids clashing with a local Postgres on 5432).
3. **pgAdmin:** register server → host `localhost`, port **5433**, user `app`, password `app` → database `system_design_copilot` (created on first container start).
4. **Migrations:** `poetry run migrate upgrade head` (uses repo `.venv`; see root `README.md`).

## Migrations (Alembic)

From **repo root** with `DATABASE_URL` set:

```bash
poetry run migrate upgrade head
poetry run migrate current
poetry run migrate history
```

Prefer **`poetry run migrate`** over `poetry run alembic …` if Conda or another env hijacks the interpreter.

New revision (review generated file before applying):

```bash
poetry run migrate revision --autogenerate -m "describe_change"
poetry run migrate upgrade head
```

Config: `apps/api/alembic.ini` · env: `apps/api/migrations/env.py`.

## Model reference (short)

| Table | ORM | Notes |
|-------|-----|--------|
| `sessions` | `DesignSession` | Conversation; `phase` e.g. product / architecture |
| `messages` | `Message` | `role`: user / assistant / system |
| `artifacts` | `Artifact` | `artifact_type`: e.g. `prd`, `system_design`, `diagram`, `roadmap`, `final_plan`; versioned |
| `event_logs` | `EventLog` | Append-only monitoring / domain events |

Use `DbSessionDep` from `app.core.deps` in routes that need a DB session.

More env vars: root `.env.example` and [PROJECT_CONTEXT.md](../../../PROJECT_CONTEXT.md).
