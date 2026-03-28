from __future__ import annotations

from pydantic import BaseModel


class VideoResponse(BaseModel):
    video_id: str
    channel_id: str | None = None
    video_url: str
    title: str | None = None
    published_at: str | None = None
    channel: str | None = None


class VideoListResponse(BaseModel):
    channel_id: str
    videos: list[VideoResponse]
