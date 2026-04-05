from __future__ import annotations

"""Phase 1 orchestration: DB → LangGraph → optional `Artifact` row.

`run_phase1_turn` is invoked from `POST .../chat` when `DesignSession.phase == "product"`.
It does not commit: the router adds the assistant `Message` and commits the whole transaction
(user message was flushed before the graph runs). If the graph wrote a PRD, `flush()` assigns IDs.
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Artifact, Message
from app.graph.phase1_product.build import build_phase1_graph
from app.graph.state.phase1 import Phase1State
from app.services.llm.openai_provider import OpenAILLMProvider

logger = logging.getLogger("app.phase1.runner")


@dataclass(frozen=True)
class Phase1RunResult:
    """Return value for the HTTP layer: assistant text + optional new PRD artifact metadata."""

    assistant_reply: str
    prd_artifact_id: UUID | None = None
    prd_version: int | None = None
    wrote_prd: bool = False


def _latest_prd_draft_seed(db: Session, session_id: UUID) -> str:
    """Pre-fill requirements_draft from the newest PRD so users can iterate after v1."""
    row = db.scalar(
        select(Artifact)
        .where(
            Artifact.session_id == session_id,
            Artifact.artifact_type == "prd",
        )
        .order_by(Artifact.version.desc())
        .limit(1)
    )
    if row is None:
        return ""
    return row.content.strip()


def _load_message_history(
    db: Session,
    session_id: UUID,
    *,
    limit: int,
) -> tuple[list[dict[str, str]], str]:
    """Load recent turns (same cap as legacy chat) and the latest user text."""
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(list(db.scalars(stmt).all())))
    history: list[dict[str, str]] = []
    last_user = ""
    for m in rows:
        if m.role not in ("user", "assistant", "system"):
            continue
        history.append({"role": m.role, "content": m.content})
        if m.role == "user":
            last_user = m.content
    return history, last_user


def _next_prd_version(db: Session, session_id: UUID) -> int:
    """Monotonic version per (session, artifact_type=prd); matches DB unique constraint."""
    current = db.scalar(
        select(func.coalesce(func.max(Artifact.version), 0)).where(
            Artifact.session_id == session_id,
            Artifact.artifact_type == "prd",
        )
    )
    return int(current or 0) + 1


async def run_phase1_turn(
    db: Session,
    session_id: UUID,
    settings: Settings,
    llm: OpenAILLMProvider,
    *,
    force_synthesize: bool,
) -> Phase1RunResult:
    """Hydrate graph state, run one compiled graph, persist new PRD artifact if synthesis ran."""
    history, user_message = _load_message_history(
        db,
        session_id,
        limit=settings.llm_context_message_limit,
    )
    draft_seed = _latest_prd_draft_seed(db, session_id)

    state: Phase1State = {
        "session_id": str(session_id),
        "user_message": user_message,
        "message_history": history,
        "requirements_draft": draft_seed,
        "open_questions": [],
        "force_synthesize": force_synthesize,
        "ready_for_prd": False,
        "assistant_reply": "",
        "prd_json": "",
    }

    graph = build_phase1_graph(
        llm,
        max_output_chars=settings.llm_max_output_chars,
        model=settings.llm_model,
    )
    out = await graph.ainvoke(state)
    assistant = (out.get("assistant_reply") or "").strip()
    prd_json = (out.get("prd_json") or "").strip()

    prd_artifact_id: UUID | None = None
    prd_version: int | None = None
    wrote = False

    if prd_json:
        version = _next_prd_version(db, session_id)
        art = Artifact(
            session_id=session_id,
            artifact_type="prd",
            version=version,
            content=prd_json,
        )
        db.add(art)
        db.flush()
        prd_artifact_id = art.id
        prd_version = version
        wrote = True
        logger.info(
            "prd_artifact_written",
            extra={"session_id": str(session_id), "version": version},
        )

    return Phase1RunResult(
        assistant_reply=assistant,
        prd_artifact_id=prd_artifact_id,
        prd_version=prd_version,
        wrote_prd=wrote,
    )
