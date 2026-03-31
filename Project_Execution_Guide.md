# Project execution guide — AI System Design Co-Pilot

This document turns [System_Design_CoPilot_Plan.md](./System_Design_CoPilot_Plan.md) into **ordered implementation steps**. Read the plan for *what* the product is; use this file for *how* to build it in a sensible order.

**How to use it:** Complete steps in order unless noted. Each step has a **goal**, **what you build**, and **done when** so you know when to move on. Skip deep polish until a thin end-to-end path works.

---

## Mindset (startup + senior engineer)

- **Vertical slice first:** One user journey (idea → saved PRD stub) beats five half-finished layers.
- **Contracts before scale:** Define API shapes and state models early; swap implementations later.
- **Observability early:** Even basic request logging helps before you debug multi-agent flows.
- **Guardrails at boundaries:** Treat every LLM and tool call as untrusted input/output from day one.

---

## Step 0 — Repository and standards

**Goal:** A clean place for backend, frontend, and infra with shared conventions.

**What you do:**

- Create a mono-repo or two-repo layout (common for startups: `apps/api`, `apps/web`, `infra/`).
- Add `.env.example` (never commit secrets). Document required keys: DB URL, LLM API keys, Kafka brokers (for later steps).
- Pick Python and Node versions; pin them (e.g. `.python-version`, `engines` in `package.json`).
- Add a minimal `README` that points to this guide and the main plan.

**Done when:** Someone can clone the repo, see where API and web live, and know which env vars exist.

---

## Step 1 — Local infrastructure (Docker Compose)

**Goal:** Databases and messaging run locally the same way every time.

**What you do:**

- Add `docker-compose.yml` with:
  - **PostgreSQL** with **pgvector** extension (matches the plan: state, metadata, RAG).
  - **Kafka** (and Zookeeper or KRaft, depending on the image you choose).
- Expose ports and volumes for data persistence during dev.
- Optional: **Redis** only if you add caching/sessions later; not required by the v1 spec.

**Done when:** `docker compose up` starts Postgres (with pgvector) and Kafka; you can connect from your machine.

---

## Step 2 — API skeleton (FastAPI)

**Goal:** A real HTTP service you can extend, not a script.

**What you do:**

- Scaffold FastAPI app: app factory, routers, dependency injection for settings.
- Endpoints: `GET /health`, `GET /ready` (ready checks DB connectivity when DB exists).
- Structured logging (JSON in prod-oriented config is fine later).
- CORS configuration placeholder for the Next.js origin.

**Done when:** You can hit health endpoints locally; configuration loads from environment.

---

## Step 3 — Database schema and migrations

**Goal:** Persistent **sessions**, **messages**, and **artifacts** (PRD, design doc, diagrams as text/JSON).

**What you do:**

- Choose an ORM or query layer (SQLAlchemy + Alembic is a common pair).
- Model at least:
  - **Project / session** — id, title, phase, timestamps.
  - **Message** — session id, role (user/assistant/system), content, metadata.
  - **Artifact** — session id, type (`prd`, `system_design`, `diagram`, `roadmap`), version, body (JSON or text).
- Run migrations against the Compose Postgres.

**Done when:** You can create a session and append messages via the API or a thin admin path.

---

## Step 4 — LLM integration (single path, no agents yet)

**Goal:** Prove end-to-end **call model → store result** before LangGraph complexity.

**What you do:**

- One service module that calls your primary model (plan references GPT-5; use whatever API you have with a **provider abstraction** so you can swap models).
- One endpoint, e.g. `POST /sessions/{id}/chat`, that:
  - Appends user message.
  - Calls the LLM with session history (bounded context).
  - Appends assistant message.
- Basic **output guardrails**: max length, strip obvious unsafe patterns, optional schema validation if you return JSON.

**Done when:** From HTTP you get a coherent reply and both messages are stored.

---

## Step 5 — LangGraph: Phase 1 (product — idea to PRD)

**Goal:** **Guided questioning** and **structured PRD** as a graph, not a single prompt.

**What you do:**

- Model state: current requirements draft, open questions, phase.
- Nodes aligned with the plan:
  - **Guided Questioning** — proposes clarifying questions or marks requirements “complete enough.”
  - **PRD synthesis** — emits structured sections: features, user stories, edge cases (JSON or markdown sections).
- Edges: loop until “complete” or user explicitly advances (your product rule).
- Replace or wrap the Step 4 chat handler to invoke this graph for **Phase 1** sessions.

**Done when:** A session in product phase produces an iterative Q&A and a storable PRD artifact.

---

## Step 6 — LangGraph: Phase 2 (architecture agents)

**Goal:** Sequential **agent pipeline** matching the workflow in the plan.

**What you do:**

- After PRD is approved (or frozen), transition session to architecture phase.
- Implement nodes (each can be a prompt + parser + validation):
  1. **Architecture Pattern** — structure, decomposition, diagram-level narrative.
  2. **Technology Expert** — stack, data stores, messaging, justification.
  3. **Scalability & Performance** — bottlenecks, scaling, data growth.
  4. **Tradeoff & Decision** — tables and rationale (CAP, cost, complexity).
  5. **Red Team** — risks, failures, weak assumptions.
- Optional **refinement loop** node that sends critiques back to earlier nodes (bounded iterations).
- Persist each major output as an **artifact** with versioning.

**Done when:** From an approved PRD you can generate a full architecture package (text artifacts); diagrams can be Mermaid strings in v1.

---

## Step 7 — Kafka event pipeline

**Goal:** **Async** fan-out matches the spec; decouple API from long-running agent runs.

**What you do:**

- Define event schemas (JSON) for: `session.created`, `message.submitted`, `agent.run.started`, `agent.run.completed`, `artifact.updated`.
- API publishes on key actions; a **worker process** (second FastAPI process or Celery-style consumer) runs LangGraph jobs triggered by events.
- Idempotency keys on handlers so retries do not duplicate work.

**Done when:** Submitting a message can return quickly while the worker completes the graph and updates DB; you can observe events in a dev tool or logs.

**Note:** If you are blocked on Kafka complexity, you may temporarily use an in-process queue **only for local demos**—but production-shaped milestones should use Kafka per the plan.

---

## Step 8 — RAG with pgvector

**Goal:** Retrieval over **past artifacts** and optional **reference docs** to ground answers.

**What you do:**

- Chunk and embed artifact text (and uploaded docs if you add uploads later).
- Store embeddings in pgvector; metadata filters by `session_id` / `project_id`.
- Retrieval tool callable from LangGraph nodes (narrow retrieval first to reduce hallucinations).

**Done when:** Agents can pull relevant chunks from prior PRD/architecture text and cite or use them in prompts.

---

## Step 9 — Observability (OpenTelemetry)

**Goal:** Trace **API → graph → LLM → tools** in one view.

**What you do:**

- Instrument FastAPI with OpenTelemetry traces.
- Wrap LLM calls and each LangGraph node with spans; attach session id as attributes.
- Export to Jaeger, Grafana Tempo, or your cloud APM (choose one for dev).

**Done when:** You can see a single trace for one user message through agents and model calls.

---

## Step 10 — Frontend (Next.js)

**Goal:** **Chat**, **document viewer**, and **diagram** display aligned with artifacts.

**What you do:**

- App shell: session list, active session, chat pane.
- Render PRD and architecture from API (markdown viewer; sanitize HTML if you render rich text).
- Mermaid (or similar) for diagrams stored as text.
- Polling or SSE/WebSocket for “run in progress” if Kafka worker is async.
- Phase indicator: Product vs Architecture.

**Done when:** A user can complete the journey in the UI without using curl.

---

## Step 11 — Quality, evaluation, and security hardening

**Goal:** Production-minded **guardrails** and **quality signals** from the plan.

**What you do:**

- **Prompt injection:** System prompts that separate instructions from user content; tool allowlists; never execute user code blindly.
- **Audit log:** Append-only record of agent decisions and tool calls (who/what/when).
- **Evaluation (incremental):** LLM-as-judge or rule checks on structured outputs; completeness checks on PRD sections.
- Rate limits and auth (even simple API keys per tenant) before any public deploy.

**Done when:** You have a checklist you run before demoing to outsiders; obvious abuse paths are reduced.

---

## Step 12 — Deployment path

**Goal:** Repeatable **prod-shaped** deploy, not only laptop Compose.

**What you do:**

- Container images for API, worker, and web.
- Managed Postgres with pgvector (or self-hosted with extension).
- Kafka cluster (managed or self-hosted); secrets via vault or platform secrets.
- Health/readiness probes, graceful shutdown for workers.

**Done when:** A staging environment runs the full path: UI → API → Kafka → worker → DB.

---

## Suggested timeline (indicative)

| Phase | Steps | Focus |
|--------|--------|--------|
| **Foundation** | 0–3 | Repo, Compose, API, DB |
| **First value** | 4–5 | LLM + Phase 1 graph |
| **Core product** | 6–8 | Phase 2 agents, Kafka, RAG |
| **Polish & ship** | 9–12 | Traces, UI, guardrails, deploy |

Adjust cadence to your team size; one strong engineer might treat each row as several days to two weeks depending on depth.

---

## Quick reference — stack (from the plan)

| Layer | Technology |
|--------|------------|
| API | FastAPI |
| Orchestration | LangGraph |
| Events | Kafka |
| Data | PostgreSQL + pgvector |
| Observability | OpenTelemetry |
| Frontend | Next.js |

---

## When you are stuck

- **Re-read** the workflow and agent list in `System_Design_CoPilot_Plan.md` sections 5–6.
- **Shrink the step:** e.g. two agents in Phase 2 before all five; Kafka after graphs work.
- **One session, one scenario:** “Build a URL shortener” end-to-end beats perfect abstraction with no user path.

This guide is a living checklist: update it when you change scope or learn something that should become a standard for the team.
