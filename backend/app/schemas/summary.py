from __future__ import annotations

from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    video_id: str
    topics: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    notable_claims: list[str] = Field(default_factory=list)
    confidence: str


class SummaryTriggerResponse(BaseModel):
    status: str
    summary: SummaryResponse
