from __future__ import annotations

from pydantic import BaseModel, Field


class ArchitecturePatternOutput(BaseModel):
    """Architecture pattern agent: structure, decomposition, diagram narrative."""

    pattern_summary: str = ""
    structural_style: str = ""
    service_decomposition: list[str] = Field(default_factory=list)
    diagram_mermaid: str = ""
    narrative: str = ""
