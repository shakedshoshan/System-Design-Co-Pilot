from __future__ import annotations

"""Phase 2 orchestration: latest PRD → LangGraph → five versioned architecture artifacts."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import Artifact
from app.graph.phase2_architecture.workflow import build_phase2_graph
from app.graph.state.phase2 import Phase2State
from app.services.llm.openai_provider import OpenAILLMProvider

logger = logging.getLogger("app.phase2.runner")

# Persisted `Artifact.artifact_type` values (stable API contract).
ARTIFACT_PATTERN = "architecture_pattern"
ARTIFACT_TECHNOLOGY = "architecture_technology"
ARTIFACT_SCALABILITY = "architecture_scalability"
ARTIFACT_TRADEOFFS = "architecture_tradeoffs"
ARTIFACT_RED_TEAM = "architecture_red_team"


@dataclass(frozen=True)
class WrittenArtifact:
    artifact_type: str
    id: UUID
    version: int


@dataclass(frozen=True)
class Phase2PipelineResult:
    """Return value for HTTP layer: summary text + written artifact metadata."""

    assistant_summary: str
    artifacts: tuple[WrittenArtifact, ...]


def session_has_prd(db: Session, session_id: UUID) -> bool:
    return _latest_prd_content(db, session_id) is not None


def _latest_prd_content(db: Session, session_id: UUID) -> str | None:
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
        return None
    return row.content.strip()


def _next_version(db: Session, session_id: UUID, artifact_type: str) -> int:
    current = db.scalar(
        select(func.coalesce(func.max(Artifact.version), 0)).where(
            Artifact.session_id == session_id,
            Artifact.artifact_type == artifact_type,
        )
    )
    return int(current or 0) + 1


def _build_assistant_summary(versions: dict[str, int]) -> str:
    lines = [
        "Architecture pipeline complete. Saved versioned artifacts:",
        f"- **{ARTIFACT_PATTERN}** (v{versions[ARTIFACT_PATTERN]})",
        f"- **{ARTIFACT_TECHNOLOGY}** (v{versions[ARTIFACT_TECHNOLOGY]})",
        f"- **{ARTIFACT_SCALABILITY}** (v{versions[ARTIFACT_SCALABILITY]})",
        f"- **{ARTIFACT_TRADEOFFS}** (v{versions[ARTIFACT_TRADEOFFS]})",
        f"- **{ARTIFACT_RED_TEAM}** (v{versions[ARTIFACT_RED_TEAM]})",
    ]
    return "\n".join(lines)


async def run_phase2_pipeline(
    db: Session,
    session_id: UUID,
    settings: Settings,
    llm: OpenAILLMProvider,
    *,
    user_notes: str = "",
) -> Phase2PipelineResult:
    prd = _latest_prd_content(db, session_id)
    if prd is None:
        raise ValueError("prd_required")

    state: Phase2State = {
        "session_id": str(session_id),
        "prd_content": prd,
        "user_notes": (user_notes or "").strip(),
        "architecture_pattern_json": "",
        "architecture_technology_json": "",
        "architecture_scalability_json": "",
        "architecture_tradeoffs_json": "",
        "architecture_red_team_json": "",
    }

    graph = build_phase2_graph(
        llm,
        max_output_chars=settings.llm_max_output_chars,
        model=settings.llm_model,
    )
    out = await graph.ainvoke(state)

    pairs: list[tuple[str, str]] = [
        (ARTIFACT_PATTERN, (out.get("architecture_pattern_json") or "").strip()),
        (ARTIFACT_TECHNOLOGY, (out.get("architecture_technology_json") or "").strip()),
        (ARTIFACT_SCALABILITY, (out.get("architecture_scalability_json") or "").strip()),
        (ARTIFACT_TRADEOFFS, (out.get("architecture_tradeoffs_json") or "").strip()),
        (ARTIFACT_RED_TEAM, (out.get("architecture_red_team_json") or "").strip()),
    ]

    written: list[WrittenArtifact] = []
    versions: dict[str, int] = {}
    for artifact_type, content in pairs:
        if not content:
            content = "{}"
        ver = _next_version(db, session_id, artifact_type)
        art = Artifact(
            session_id=session_id,
            artifact_type=artifact_type,
            version=ver,
            content=content,
        )
        db.add(art)
        db.flush()
        versions[artifact_type] = ver
        written.append(WrittenArtifact(artifact_type=artifact_type, id=art.id, version=ver))
        logger.info(
            "phase2_artifact_written",
            extra={"session_id": str(session_id), "type": artifact_type, "version": ver},
        )

    summary = _build_assistant_summary(versions)
    return Phase2PipelineResult(
        assistant_summary=summary,
        artifacts=tuple(written),
    )
