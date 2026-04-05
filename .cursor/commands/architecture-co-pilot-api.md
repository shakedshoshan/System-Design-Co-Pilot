# Architecture Co-Pilot API

Use the project skill **architecture-co-pilot-api** (`.cursor/skills/architecture-co-pilot-api/SKILL.md`).

1. **Code:** Add routes under `apps/api/app/routers/architecture_copilot/` (sub-routers + `router.py`), prefix `/api/v1`, envelopes + `AppError` per existing API patterns.
2. **Postman:** Use MCP **user-postman-mcp** (read tool schemas first). Target workspace **`architecture-co-pilot`**; collection **Architecture Co-Pilot**; environment **Architecture Co-Pilot — local** with `baseUrl`. Use `import_collection_from_file` + `targetWorkspaceId` when bootstrapping from repo JSON.
3. **Repo:** Optional exports in `architecture-co-pilot/postman/collections/`.
4. **Docs:** Update `PROJECT_CONTEXT.md` API table when routes are finalized.
