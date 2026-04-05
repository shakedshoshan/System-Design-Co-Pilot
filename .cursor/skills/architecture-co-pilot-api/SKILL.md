---
name: architecture-co-pilot-api
description: >-
  Adds or updates FastAPI endpoints under the architecture-co-pilot surface and
  mirrors them in Postman with a consistent folder layout. Use when the user asks
  to add API routes, sync Postman, scaffold architecture-co-pilot endpoints, or
  mentions the Architecture Co-Pilot API collection.
---

# Architecture Co-Pilot API endpoints + Postman

## Repo layout (do not flatten)

| Area | Path | Purpose |
|------|------|---------|
| FastAPI routes (Python package) | `apps/api/app/routers/architecture_copilot/` | New endpoints: one module per domain (e.g. `sessions.py`, `artifacts.py`) re-exporting routes on `router`. |
| Postman exports / backups | `architecture-co-pilot/postman/collections/` | Optional committed exports (`export_collection` MCP or Postman app). |
| This workflow | `.cursor/skills/architecture-co-pilot-api/SKILL.md` | Source of truth for steps below. |

**Naming:** URL path segments and Postman folders use **kebab-case**; Python modules use **snake_case** (`sessions.py` → folder `sessions` or `Sessions` in Postman—pick one per collection and stay consistent; default **PascalCase folder names** in Postman for readability).

## FastAPI rules (match existing API)

1. Read `PROJECT_CONTEXT.md` and existing `app/schemas/responses.py`, `app/http/errors.py`, `app/core/exceptions.py`.
2. Mount domain routers on **`router`** in `apps/api/app/routers/architecture_copilot/router.py` (already included from `main.py` with prefix **`/api/v1`**).
3. Success responses: return **`SuccessEnvelope`** / **`success_body`** with `Meta(request_id=request_id)` and **`RequestIdDep`** where handlers return JSON bodies.
4. Domain failures: raise **`AppError`** (or `HTTPException` only when mapping to standard HTTP semantics without a product code).
5. Request/response DTOs: prefer `app/schemas/` (domain subfolder later, e.g. `app/schemas/architecture_copilot/`)—keep routers thin.
6. Register sub-routers in `architecture_copilot/router.py`:
   `router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])`.

## Postman MCP (required for this workflow)

**Server:** `user-postman-mcp` (read tool schemas under the workspace `mcps/user-postman-mcp/tools/` before the first call).

**Typical flow**

1. **`list_workspaces`** — use workspace named **`architecture-co-pilot`** as `workspaceId` for this project (create with **`create_workspace`** `name: "architecture-co-pilot"`, `type: "personal"` if it does not exist).
2. **`list_collections`** with that `workspaceId` — find collection **`Architecture Co-Pilot`**. If missing: **`create_collection`** with `workspaceId` set to the architecture-co-pilot workspace.
3. **`get_collection`** — if `item` is **empty** after a file import, do **not** rely on import alone: use **`create_folder`** + **`create_request`** (see below). **`import_collection_from_file`** has been observed to create an empty collection in Postman Cloud.
4. **Folders:** **`create_folder`** with `collectionId`; use **`parentFolderId`** for nesting. Recommended top-level folders:
   - **`System`** — root routes: `/health`, `/ready`, `/openapi.json` (not under `/api/v1`).
   - **`API v1`** — product routes; optional nested folders per domain (`Sessions`, `Messages`, …).
5. **Requests:** **`create_request`** with `collectionId`, `name`, `method`, `url`, `folderId`, `description`, `headers`.
   - URLs: `{{baseUrl}}/health`, `{{baseUrl}}/api/v1/...`, etc.
   - **Quirk:** after **`create_request`**, **`get_collection`** may show `url.raw` empty until you call **`update_request`** with the same `url` string again—**always run `update_request`** to fix URLs if the UI shows a blank address bar.
   - Headers: `Accept: application/json`; optional `X-Request-ID` (can be `disabled: true` with empty value).
6. **Environment:** if missing, **`create_environment`** with `name: "Architecture Co-Pilot — local"`, `workspaceId`, and `values` including at least:
   - `baseUrl` = `http://127.0.0.1:8000`
   - (later) `bearerToken` or API keys as `type: "secret"` where appropriate.

**Maintenance:** use **`update_request`**, **`update_folder`**, **`move_request`**, **`delete_request`** / **`delete_folder`** to keep Postman aligned with code changes. Optionally **`export_collection`** and save JSON under `architecture-co-pilot/postman/collections/` for version control.

## Checklist per new endpoint

- [ ] Handler in `architecture_copilot/` (or included sub-router), typed models, envelope/error pattern.
- [ ] `PROJECT_CONTEXT.md` API table row updated if the route is stable.
- [ ] Postman: request under the correct folder; URL + method + sample body; environment variables used.
- [ ] Optional: export collection to `architecture-co-pilot/postman/collections/`.

## Slash command

Users can run **`/architecture-co-pilot-api`** (`.cursor/commands/architecture-co-pilot-api.md`) for a short reminder; follow this skill for full behavior.
