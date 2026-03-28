from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.session import get_db
from app.schemas.channel import ChannelCreateRequest, ChannelResponse
from app.schemas.video import VideoListResponse, VideoResponse
from app.services.youtube_service import ChannelNotFoundError, youtube_service


router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("", response_model=ChannelResponse)
def create_channel(payload: ChannelCreateRequest, db: Session = Depends(get_db)) -> ChannelResponse:
    try:
        channel = youtube_service.register_channel(db, payload.url_or_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ChannelResponse(id=channel.id, name=channel.name, url=channel.url)


@router.get("", response_model=list[ChannelResponse])
def list_channels(db: Session = Depends(get_db)) -> list[ChannelResponse]:
    channels = youtube_service.list_channels(db)
    return [ChannelResponse(id=channel.id, name=channel.name, url=channel.url) for channel in channels]


@router.get("/{channel_id}/videos", response_model=VideoListResponse)
def list_channel_videos(
    channel_id: str,
    max_per_channel: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> VideoListResponse:
    try:
        videos = youtube_service.list_channel_videos(
            db=db,
            channel_id=channel_id,
            max_per_channel=max_per_channel,
        )
    except ChannelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return VideoListResponse(
        channel_id=channel_id,
        videos=[
            VideoResponse(
                video_id=video.video_id,
                channel_id=channel_id,
                video_url=video.video_url,
                title=video.title,
                published_at=video.published_at,
                channel=video.channel,
            )
            for video in videos
        ],
    )
