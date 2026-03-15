from __future__ import annotations

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    video_id: str
    video_url: str
    title: str | None = None
    published_at: str | None = None


class DiscoveryResult(BaseModel):
    videos: list[VideoMetadata] = Field(default_factory=list)
    skipped_sources: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class TranscriptSegment(BaseModel):
    start: float
    duration: float
    text: str


class RawVideoRecord(BaseModel):
    metadata: VideoMetadata
    transcript_segments: list[TranscriptSegment] = Field(default_factory=list)
    transcript_status: str
    transcript_detail: str | None = None


class TranscriptFetchResult(BaseModel):
    fetched_records: list[RawVideoRecord] = Field(default_factory=list)
    missing_transcripts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PerVideoSummary(BaseModel):
    video_id: str
    topics: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    notable_claims: list[str] = Field(default_factory=list)
    confidence: str = "MEDIUM"


class SummaryGenerationResult(BaseModel):
    summaries: list[PerVideoSummary] = Field(default_factory=list)
    skipped_videos: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
