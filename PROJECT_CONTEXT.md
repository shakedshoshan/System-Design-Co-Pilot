# Project context — living build map

**Purpose:** Short, accurate picture of **what exists in the repo** (layout, key files, env, status). Use this before coding; keep it **minimal**—no full PRD here.

**Related docs:** [System_Design_CoPilot_Plan.md](./System_Design_CoPilot_Plan.md) (product/spec), [Project_Execution_Guide.md](./Project_Execution_Guide.md) (build order).

**LangGraph walkthroughs (API app):** [Phase 1 — product → PRD](./apps/api/app/graph/docs/Phase1_Product_LangGraph_Flow.md), [Phase 2 — architecture agents](./apps/api/app/graph/docs/Phase2_Architecture_LangGraph_Flow.md).

**Last updated:** 2026-04-06 (graph `workflow.py` / `edges.py` / `routing.py`, folder tree)

---

## Implementation status

| Area | Status | Notes |
|------|--------|--------|
| Repo / tooling | Step 0 done | `.env.example`, `.python-version`, `apps/api/pyproject.toml`, `apps/web/package.json` engines, root `README` + `.gitignore` |
| Docker (Postgres+pgvector, Kafka) | Step 1 done | Root `docker-compose.yml` — Postgres on **host `127.0.0.1:5433`** → container 5432; Kafka KRaft `localhost:9092`; pgvector init under `infra/docker/postgres/init/` |
| FastAPI API | Step 2+ infra | Envelopes + `http/errors.py`, `middleware/` (request id, access log), rotating JSON `logs/app.log` |
| DB models / migrations | Step 3 done | SQLAlchemy 2.x + Alembic; tables `sessions`, `messages`, `artifacts`, `event_logs`; `apps/api/migrations/versions/20260405_0001_*.py` |
| LLM integration | Step 4+5 | OpenAI `AsyncOpenAI` + `OpenAILLMProvider`; guardrails in `app/services/llm/guardrails.py` |
| LangGraph Phase 1 (PRD) | Step 5 done | `session.phase == "product"` → `app/graph/phase1_product` (guided Q + PRD synthesis) via `app/services/phase1/runner.py`; `artifact_type=prd` versioned rows |
| LangGraph Phase 2 (agents) | Step 6 done | `PATCH /api/v1/sessions/{id}` → `phase=architecture` (needs PRD); `POST .../architecture/run` runs graph; `app/graph/phase2_architecture/` + `app/services/phase2/runner.py`; five `architecture_*` artifact types; flow [Phase2 doc](./apps/api/app/graph/docs/Phase2_Architecture_LangGraph_Flow.md) |
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
├── devtools/                     # `run_api`, `run_migrate` (Poetry scripts)
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
│   │   │   ├── schemas/        # API envelopes + `architecture_copilot/` DTOs
│   │   │   ├── routers/        # HTTP routes (+ architecture_copilot/ → /api/v1)
│   │   │   ├── services/       # Orchestration helpers
│   │   │   │   ├── llm/        # Provider abstraction, calls
│   │   │   │   ├── phase1/     # Product-phase graph runner (hydrate state, PRD artifact)
│   │   │   │   ├── phase2/     # Architecture pipeline (five agents → artifacts)
│   │   │   │   └── rag/        # Embeddings retrieval (pgvector)
│   │   │   ├── graph/          # LangGraph: compiled graphs, wiring
│   │   │   │   ├── docs/       # Phase1_Product_LangGraph_Flow.md, Phase2_Architecture_LangGraph_Flow.md
│   │   │   │   ├── state/      # Shared graph state (`phase1`, `phase2` TypedDicts)
│   │   │   │   ├── phase1_product/   # workflow.py, edges.py, routing.py, nodes — idea → PRD
│   │   │   │   └── phase2_architecture/  # workflow.py, edges.py; nodes/, prompts/, schemas/, parsing/ (README)
│   │   │   ├── agents/         # Reserved (empty); phase agents live under graph/phase*_*/
│   │   │   ├── db/             # Base, `models/`, session, `schema.sql` — see `app/db/README.md`
│   │   │   ├── kafka/          # Producers (events to worker / bus)
│   │   │   └── observability/  # OpenTelemetry setup, instrumentation helpers
│   │   ├── migrations/         # Alembic (`versions/`); not named `alembic` — avoids shadowing the PyPI package
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
└── scripts/                    # `docker_up_postgres.ps1`
```

**Current repo:** Step 6 complete (architecture phase + five-agent graph). Next: Step 7 (Kafka) or Next.js.

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
| `OPENAI_API_KEY` | API | OpenAI API key (required for chat) |
| `LLM_MODEL` | API | Default chat model (default `gpt-4o`) |
| `LLM_TIMEOUT_SECONDS` | API | OpenAI client timeout per request (default `120`); Phase 2 runs five calls in one HTTP request — increase if needed |
| `LLM_CONTEXT_MESSAGE_LIMIT` | API | Max prior messages sent to the model (default `50`) |
| `LLM_MAX_OUTPUT_CHARS` | API | Assistant reply cap after sanitization (default `32000`) |
| `KAFKA_BOOTSTRAP_SERVERS` | API, worker | Kafka brokers |
| `CORS_ORIGINS` | API | Allowed browser origins (comma-separated) |
| `NEXT_PUBLIC_API_URL` | Web | FastAPI base URL (browser) |
| `API_HOST`, `API_PORT` | API | Bind address (optional defaults in code later) |
| `OTEL_*` | API, worker | OpenTelemetry (later) |

---

## API surface (architecture-co-pilot `/api/v1`)

Update when routes change.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness — body `{ data, meta }` |
| GET | `/ready` | Readiness — same envelope; 503 uses `{ error, meta }` |
| POST | `/api/v1/sessions` | Create `DesignSession` — body `{ title? }`, returns `data.session` |
| POST | `/api/v1/sessions/{session_id}/chat` | Body `{ content, product_action? }` (`default` \| `synthesize_prd`). If `phase` is `product`: LangGraph guided Q → optional PRD synthesis; else single-call chat (Step 4). Returns `data.chat` with optional `prd_artifact_id`, `prd_version`, `phase1_ready_for_architecture` |
| PATCH | `/api/v1/sessions/{session_id}` | Body `{ "phase": "architecture" }` — requires a `prd` artifact; idempotent if already `architecture`. Returns `data.session` |
| POST | `/api/v1/sessions/{session_id}/architecture/run` | Body `{ notes? }`. Requires `phase=architecture` and PRD. Runs Phase 2 LangGraph; returns `data.architecture_run` (artifact refs + assistant message ids) |

---

## Important parts (short notes)

Add one-line pointers as you implement—**only** what helps the next developer find logic quickly.

| Topic | Location | Note |
|-------|----------|------|
| Local DB + Kafka | `docker-compose.yml` | `postgres` (pgvector), `kafka`; see root `README.md` |
| Run API | repo root or `apps/api` | **Poetry:** `poetry install` then `poetry run api` (`.venv/` at root). **pip:** `apps/api` venv + `uvicorn app.main:app --reload`. Env: repo root `.env` |
| Database | `app/db/README.md`, `app/db/schema.sql` | ORM; readable DDL snapshot (`schema.sql` ↔ initial migration); `poetry run migrate …` |
| ORM models | `app/db/models/__init__.py` | `DesignSession`, `Message`, `Artifact`, `EventLog` |
| Alembic | repo root | `poetry run migrate upgrade head` — `devtools/run_migrate.py` → `.venv` + `alembic -c apps/api/alembic.ini` |
| API errors / correlation | `app/http/errors.py`, `middleware/` | `AppError`, validation + 500 handlers; `X-Request-ID` header |
| Log files | `apps/api/logs/app.log` | JSON lines (rotation); gitignored |
| New product endpoints + Postman | `.cursor/skills/architecture-co-pilot-api/`, `architecture-co-pilot/` | Postman workspace **`architecture-co-pilot`**; collection **Architecture Co-Pilot**; env **Architecture Co-Pilot — local**; repo `postman/collections/*.json` |
| LLM (OpenAI) | `app/services/llm/`, `app/main.py` lifespan | `AsyncOpenAI` in app lifespan; `OpenAILLMProvider.chat_completion`; `get_llm_provider` in `core/deps.py` |
| LangGraph Phase 1 | `app/graph/phase1_product/` (`workflow.py`, `edges.py`, `routing.py`, `nodes.py`), `app/services/phase1/runner.py` | `build_phase1_graph()`; product-phase chat in `routers/architecture_copilot/sessions.py`; [Phase1_Product_LangGraph_Flow.md](./apps/api/app/graph/docs/Phase1_Product_LangGraph_Flow.md) |
| LangGraph Phase 2 | `app/graph/phase2_architecture/README.md`, `app/services/phase2/runner.py`, `app/graph/state/phase2.py` | `build_phase2_graph()`; `workflow.py` + `edges.py` · `nodes/` · `prompts/` · `schemas/` · `parsing/`; [Phase2_Architecture_LangGraph_Flow.md](./apps/api/app/graph/docs/Phase2_Architecture_LangGraph_Flow.md); `sessions.py`: PATCH + `POST .../architecture/run` |
| Phase 2 unit tests | `apps/api/tests/unit/test_phase2_graph.py`, `test_phase2_runner.py` | Mock LLM / DB; `poetry run pytest` |
| API tests | root `pyproject.toml` `[tool.pytest.ini_options]`, `apps/api/tests/` | `poetry run pytest` |

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
