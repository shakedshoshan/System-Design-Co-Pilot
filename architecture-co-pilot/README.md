# Architecture Co-Pilot (API workspace)

This folder groups **API contract artifacts** for the System Design Co-Pilot backend. Application code lives under `apps/api/`; this tree is for Postman exports and related assets.

## Layout

```text
architecture-co-pilot/
├── README.md                 # This file
└── postman/
    └── collections/          # Optional: Postman collection JSON exports (MCP export_collection or app export)
```

## Workflow

Use the Cursor skill **`architecture-co-pilot-api`** or slash command **`/architecture-co-pilot-api`** so new endpoints are implemented in `apps/api/app/routers/architecture_copilot/` and mirrored in Postman via **Postman MCP** (`user-postman-mcp`) with a consistent folder structure.

## Postman

**Workspace (canonical):** switch to **`architecture-co-pilot`** in Postman (workspace switcher, top left). This is where the API collection and local environment are kept in sync via MCP.

**In that workspace you should see**

- **Collection:** **Architecture Co-Pilot** — folders **System** (**Health**, **Ready**, **OpenAPI JSON**) and **API v1** → **Sessions** (**Create session**, **Chat (Step 4)**).
- **Environment:** **Architecture Co-Pilot — local** — variables **`baseUrl`** = `http://127.0.0.1:8000`, **`sessionId`** = (paste UUID from Create session). Select it in the environment dropdown before sending requests.

**Repo copies (import anywhere):** `postman/collections/Architecture-Co-Pilot.postman_collection.json` and `postman/collections/local.postman_environment.json`. Note: Postman Cloud sometimes imports that file as an **empty** collection; the canonical fix is recreating folders/requests via MCP (`create_folder`, `create_request`, then `update_request` for URLs)—see skill **architecture-co-pilot-api**.

**Older duplicate:** an earlier **Architecture Co-Pilot** collection may still exist under another workspace; you can delete it to avoid confusion.

**If you don’t see the workspace:** confirm you’re signed into Postman with the **same account** as the Postman API key used for Cursor MCP, then use **Ctrl+K** / **Cmd+K** and search **`architecture-co-pilot`**.
