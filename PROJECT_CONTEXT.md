# Project context — living build map

**Purpose:** Short, accurate picture of **what exists in the repo** (layout, key files, env, status). Use this before coding; keep it **minimal**—no full PRD here.

**Related docs:** [System_Design_CoPilot_Plan.md](./System_Design_CoPilot_Plan.md) (product/spec), [Project_Execution_Guide.md](./Project_Execution_Guide.md) (build order).

**Last updated:** 2026-04-05 (Root Poetry: `pyproject.toml`, `poetry.toml`, `devtools/run_api`, script `poetry run api`)

---

## Implementation status

| Area | Status | Notes |
|------|--------|--------|
| Repo / tooling | Step 0 done | `.env.example`, `.python-version`, `apps/api/pyproject.toml`, `apps/web/package.json` engines, root `README` + `.gitignore` |
| Docker (Postgres+pgvector, Kafka) | Step 1 done | Root `docker-compose.yml`; `infra/docker/postgres/init/01-pgvector.sql`; Apache Kafka 3.9.x KRaft on `localhost:9092` |
| FastAPI API | Step 2+ infra | Envelopes + `http/errors.py`, `middleware/` (request id, access log), rotating JSON `logs/app.log` |
| DB models / migrations | Not started | |
| LLM integration | Not started | |
| LangGraph Phase 1 (PRD) | Not started | |
| LangGraph Phase 2 (agents) | Not started | |
| Kafka + worker | Not started | |
| RAG / pgvector usage | Not started | |
| OpenTelemetry | Not started | |
| Next.js frontend | Not started | |
| Auth / guardrails / deploy | Not started | |

---

## Stack (v1 target)

- API: **FastAPI** · Orchestration: **LangGraph** · Events: **Kafka** · Data: **PostgreSQL + pgvector** · Observability: **OpenTelemetry** · Frontend: **Next.js**

---

## Folder structure

Adjust this tree when you create or rename paths. Omit `__pycache__`, `node_modules`, `.next`, etc.

```text
System Design Co-Pilot/
├── .cursor/
│   ├── rules/
│   ├── commands/               # Slash commands (align-with-plan, architecture-co-pilot-api, …)
│   └── skills/
│       └── architecture-co-pilot-api/   # SKILL.md — API + Postman MCP workflow
├── PROJECT_CONTEXT.md
├── System_Design_CoPilot_Plan.md
├── Project_Execution_Guide.md
├── .env.example                  # Documented vars (no secrets)
├── .gitignore
├── .python-version               # 3.12.x (API + worker)
├── pyproject.toml                # Poetry (root venv + path dep apps/api)
├── poetry.toml                   # virtualenv in-project → .venv/
├── devtools/                     # `run_api` console entry for `poetry run api`
├── README.md
├── architecture-co-pilot/        # Postman exports + API workspace docs (see README there)
├── docker-compose.yml            # Postgres+pgvector, Kafka (KRaft)
├── apps/
│   ├── api/                      # FastAPI — HTTP, DB, LangGraph entry from API
│   │   ├── app/
│   │   │   ├── main.py         # App factory, CORS, mounts routers
│   │   │   ├── core/           # Settings, config, lifespan hooks
│   │   │   ├── http/           # Exception handlers → unified error JSON
│   │   │   ├── middleware/     # X-Request-ID, structured access log
│   │   │   ├── schemas/        # API envelopes (success/error + meta)
│   │   │   ├── routers/        # HTTP routes (+ architecture_copilot/ → /api/v1)
│   │   │   ├── services/       # Orchestration helpers
│   │   │   │   ├── llm/        # Provider abstraction, calls
│   │   │   │   └── rag/        # Embeddings retrieval (pgvector)
│   │   │   ├── graph/          # LangGraph: compiled graphs, wiring
│   │   │   │   ├── state/      # Shared graph state schemas
│   │   │   │   ├── phase1_product/   # Idea → PRD (guided Q, synthesis)
│   │   │   │   └── phase2_architecture/  # Agent pipeline (pattern, tech, scale, tradeoffs, red team)
│   │   │   ├── agents/         # Agent node builders, prompts, tools per role
│   │   │   ├── db/             # Session, SQLAlchemy models, repos
│   │   │   ├── schemas/        # Pydantic request/response DTOs
│   │   │   ├── kafka/          # Producers (events to worker / bus)
│   │   │   └── observability/  # OpenTelemetry setup, instrumentation helpers
│   │   ├── alembic/            # Migrations (`versions/`)
│   │   ├── pyproject.toml      # Python project + `requires-python`
│   │   └── tests/              # `unit/`, `integration/`
│   ├── worker/                 # Kafka consumers — long-running agent jobs
│   │   ├── app/
│   │   │   ├── consumers/      # Subscriber loops / consumer groups
│   │   │   └── handlers/       # Per-topic handlers → graph or services
│   │   └── tests/
│   └── web/                    # Next.js (App Router under `app/`)
│       ├── package.json        # `engines.node` pinned
│       ├── .nvmrc              # Node 20.x (optional; nvm/fnm)
│       ├── app/
│       ├── components/         # ui/, chat/, diagrams/, layout/
│       ├── lib/api/            # Typed fetch / API client
│       ├── hooks/
│       ├── public/
│       └── styles/
├── packages/
│   └── contracts/              # (optional) OpenAPI-generated types shared with web
├── infra/
│   ├── docker/                 # Dockerfiles per service; postgres/init → pgvector enable
│   └── kubernetes/             # Kustomize-style: base/, overlays/dev|prod/
└── scripts/                    # Dev, migrate, seed helpers
```

**Current repo:** Step 2 complete (API skeleton). Next: Step 3 (DB models + Alembic), scaffold Next when you start the web app.

---

## Frontend / backend separation

The repo is a **monorepo with two deployable applications**, not a single combined process:

| Layer | Location | Owns |
|--------|-----------|------|
| **Backend** | `apps/api` (+ `apps/worker`) | HTTP API, DB, migrations, LangGraph, LLM/RAG, Kafka producers/consumers, OpenTelemetry for server-side work |
| **Frontend** | `apps/web` | UI (App Router), React components, browser-only concerns; calls the API over HTTP |

**Rules of thumb**

- **Authoritative domain logic** (sessions, messages, artifacts, agents, streaming) lives in **FastAPI** (and worker), not in Next.js Route Handlers. Next.js may use [Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers) only as an optional **BFF** (e.g. proxy, cookie/session bridging)—not as a second implementation of orchestration.
- **Contract between them**: HTTP + OpenAPI from FastAPI; optional generated types for the web app under `packages/contracts` so the frontend does not guess request/response shapes.
- **Browser → API connectivity** (different origins in dev: e.g. `localhost:3000` vs `localhost:8000`):
  - **FastAPI**: use `CORSMiddleware` with an explicit `allow_origins` list (include the Next.js dev URL); avoid `allow_origins=["*"]` if you use cookies or `Authorization` (per FastAPI CORS docs).
  - **Next.js**: either call the API via a public base URL (e.g. `NEXT_PUBLIC_API_URL`) or use **`rewrites` in `next.config`** to proxy a path prefix to the backend (same-origin to the browser, fewer CORS preflights). Choose one approach per environment and document it in `.env.example`.

`packages/` and `infra/docker` stay **shared tooling / deploy**, not a third runtime tier.

---

## Environment variables

See root [`.env.example`](./.env.example) for descriptions. Summary:

| Variable | Used by | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | API, Alembic | PostgreSQL connection |
| `APP_ENV` | API | `local` (default) or `production` — stdout format + hides internal errors when `production` |
| `LOG_TO_FILE`, `LOG_FILE`, `LOG_LEVEL`, `LOG_MAX_MB`, `LOG_BACKUP_COUNT` | API | Rotating JSON logs under `apps/api/logs` (default on) |
| `OPENAI_API_KEY` | API | LLM provider (Step 4+) |
| `KAFKA_BOOTSTRAP_SERVERS` | API, worker | Kafka brokers |
| `CORS_ORIGINS` | API | Allowed browser origins (comma-separated) |
| `NEXT_PUBLIC_API_URL` | Web | FastAPI base URL (browser) |
| `API_HOST`, `API_PORT` | API | Bind address (optional defaults in code later) |
| `OTEL_*` | API, worker | OpenTelemetry (later) |

---

## API surface (planned)

Update when routes exist.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness — body `{ data, meta }` |
| GET | `/ready` | Readiness — same envelope; 503 uses `{ error, meta }` |
| _TBD_ | _TBD_ | _TBD_ |

---

## Important parts (short notes)

Add one-line pointers as you implement—**only** what helps the next developer find logic quickly.

| Topic | Location | Note |
|-------|----------|------|
| Local DB + Kafka | `docker-compose.yml` | `postgres` (pgvector), `kafka`; see root `README.md` |
| Run API | repo root or `apps/api` | **Poetry:** `poetry install` then `poetry run api` (`.venv/` at root). **pip:** `apps/api` venv + `uvicorn app.main:app --reload`. Env: repo root `.env` |
| API errors / correlation | `app/http/errors.py`, `middleware/` | `AppError`, validation + 500 handlers; `X-Request-ID` header |
| Log files | `apps/api/logs/app.log` | JSON lines (rotation); gitignored |
| New product endpoints + Postman | `.cursor/skills/architecture-co-pilot-api/`, `architecture-co-pilot/` | Postman workspace **`architecture-co-pilot`**; collection **Architecture Co-Pilot**; env **Architecture Co-Pilot — local**; repo `postman/collections/*.json` |

---

## Conventions

- **Python:** 3.12.x recommended (`.python-version`); **3.11+** allowed (`pyproject.toml` / `apps/api` for local Poetry/pip)
- **Node:** ≥20.10 (`apps/web/package.json` `engines`)
- **TypeScript / lint:** _TBD_ when Next.js is scaffolded
- **Branching / commits:** _TBD_
- **Web env:** `NEXT_PUBLIC_API_URL` and optional `API_INTERNAL_URL`; **API:** `CORS_ORIGINS` matching the Next.js origin(s)

---

## Maintenance

The AI assistant should update this file **only when necessary** after code changes (new folders/files, env vars, routes, major modules). See `.cursor/rules/project-context.mdc`.
