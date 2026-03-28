from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ChannelModel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    videos: Mapped[list["VideoModel"]] = relationship(
        "VideoModel",
        back_populates="channel",
        cascade="all, delete-orphan",
    )


class VideoModel(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    channel: Mapped[ChannelModel] = relationship("ChannelModel", back_populates="videos")
    summaries: Mapped[list["SummaryModel"]] = relationship(
        "SummaryModel",
        back_populates="video",
        cascade="all, delete-orphan",
    )


class SummaryModel(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), nullable=False, index=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    video: Mapped[VideoModel] = relationship("VideoModel", back_populates="summaries")
