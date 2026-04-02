from __future__ import annotations

import logging
import re
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from mindstream.ingest.youtube_discovery import discover_videos, fetch_video_metadata
from mindstream.storage.models import VideoMetadata

from app.db.models import ChannelModel, VideoModel


class ChannelNotFoundError(ValueError):
    """Raised when a channel identifier is unknown."""


logger = logging.getLogger(__name__)


class YouTubeService:
    VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

    def register_channel(self, db: Session, url_or_name: str) -> ChannelModel:
        source = self._normalize_source(url_or_name)
        channel = ChannelModel(
            id=uuid4().hex,
            name=self._display_name(url_or_name),
            url=source,
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)
        logger.info("Channel created: id=%s url=%s", channel.id, channel.url)
        return channel

    def list_channels(self, db: Session) -> list[ChannelModel]:
        return db.query(ChannelModel).order_by(ChannelModel.created_at.desc()).all()

    def list_channel_videos(self, db: Session, channel_id: str, max_per_channel: int = 5) -> list[VideoMetadata]:
        channel = db.get(ChannelModel, channel_id)
        if channel is None:
            raise ChannelNotFoundError(f"Channel '{channel_id}' was not found.")

        result = discover_videos([channel.url], max_per_channel=max_per_channel)
        if result.errors:
            raise ValueError("; ".join(result.errors))
        if not result.videos:
            raise ValueError(f"No videos found for source '{channel.url}'.")

        for video in result.videos:
            self._upsert_video(db, channel.id, video)
            logger.info("Video fetched: id=%s channel_id=%s", video.video_id, channel.id)
        db.commit()
        return result.videos

    def get_video(self, db: Session, video_id: str) -> VideoMetadata:
        stored = db.get(VideoModel, video_id)
        if stored is not None:
            channel = db.get(ChannelModel, stored.channel_id)
            return VideoMetadata(
                video_id=stored.id,
                video_url=f"https://www.youtube.com/watch?v={stored.id}",
                title=stored.title,
                published_at=stored.published_at.isoformat() if stored.published_at else None,
                channel=channel.name if channel else None,
            )

        if not self._looks_like_video_id(video_id):
            raise HTTPException(status_code=404, detail="Video not found")

        canonical = VideoMetadata(
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            title=None,
            published_at=None,
            channel=None,
        )
        enriched = fetch_video_metadata(canonical)
        if not self._is_resolved_video(enriched):
            raise HTTPException(status_code=404, detail="Video not found")
        return enriched

    @staticmethod
    def _upsert_video(db: Session, channel_id: str, video: VideoMetadata) -> VideoModel:
        published_at = YouTubeService._parse_published_at(video.published_at)
        title = (video.title or "").strip() or video.video_id
        stored = db.get(VideoModel, video.video_id)
        if stored is None:
            stored = VideoModel(
                id=video.video_id,
                channel_id=channel_id,
                title=title,
                published_at=published_at,
            )
            db.add(stored)
            return stored

        stored.channel_id = channel_id
        stored.title = title
        stored.published_at = published_at
        return stored

    @staticmethod
    def _normalize_source(url_or_name: str) -> str:
        source = url_or_name.strip()
        if not source:
            raise ValueError("Channel URL or name is required.")
        if source.startswith("http://") or source.startswith("https://"):
            return source
        if source.startswith("@"):
            return f"https://www.youtube.com/{source}"
        return f"https://www.youtube.com/@{source}"

    @staticmethod
    def _display_name(url_or_name: str) -> str:
        source = url_or_name.strip()
        if source.startswith("http://") or source.startswith("https://"):
            return source.rstrip("/").rsplit("/", 1)[-1] or source
        return source.lstrip("@")

    @staticmethod
    def _looks_like_video_id(video_id: str) -> bool:
        return bool(YouTubeService.VIDEO_ID_PATTERN.fullmatch(video_id.strip()))

    @staticmethod
    def _is_resolved_video(video: VideoMetadata) -> bool:
        return bool((video.title or "").strip() or (video.published_at or "").strip() or (video.channel or "").strip())

    @staticmethod
    def _parse_published_at(value: str | None) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None


youtube_service = YouTubeService()
