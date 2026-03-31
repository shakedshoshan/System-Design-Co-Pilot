# Optimize conversation build

Use this **after** the assistant (or you) has implemented something in the **current chat**. It drives a second pass: critical review, optimization, and fixes—scoped to what this conversation actually produced.

## Scope

1. **Identify the build** — List files created or materially changed in this conversation (from chat history and diffs). If unclear, ask once which paths count.
2. **Read before changing** — Open those files and surrounding call sites; do not optimize from memory alone.

## Critical review (think, then act)

Work through these in order; note findings briefly before editing.

- **Intent vs implementation** — Does the code match what the user asked for in this thread? Any missing behavior or wrong assumptions?
- **Correctness** — Edge cases, error paths, null/empty inputs, concurrency or idempotency if relevant.
- **Project fit** — Match `PROJECT_CONTEXT.md`, stack boundaries (API vs web vs worker), and existing patterns in touched packages.
- **Security & data** — Secrets not hardcoded; validation on boundaries; least privilege for new access patterns.
- **Maintainability** — Duplication vs existing helpers; naming and types; avoid drive-by refactors **outside** the conversation scope.

## Optimize

Apply only where it clearly helps the scoped code:

- Simpler control flow, fewer layers, clearer data shapes.
- Performance hotspots only if justified (measure or obvious N+1 / redundant work).
- Lint/type issues introduced by this build; run project checks if available (`ruff`, `mypy`, `eslint`, tests for touched areas).

## Fix and report

- **Fix** issues found in the review or checks; keep diffs minimal and tied to this conversation’s code.
- **Summarize** for the user: what was wrong or suboptimal, what you changed, and what you left as follow-up (if any) with reason.

Do **not** rewrite unrelated files or expand scope beyond what this conversation built unless the user explicitly widens it.
