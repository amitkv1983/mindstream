from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy.orm import Session

from mindstream.process.summarize_video import generate_summaries
from mindstream.storage.local_store import ensure_data_dirs
from mindstream.storage.models import PerVideoSummary

from app.core.config import settings
from app.db.models import SummaryModel, VideoModel
from app.services.transcript_service import transcript_service
from app.services.youtube_service import youtube_service


class SummaryNotReadyError(ValueError):
    """Raised when a stored summary does not exist."""


class SummarizerServiceError(RuntimeError):
    """Raised when summary generation fails."""


class SummarizerService:
    def __init__(self) -> None:
        ensure_data_dirs(settings.project_id)

    def summarize_video(self, db: Session, video_id: str) -> PerVideoSummary:
        stored_video = db.get(VideoModel, video_id)
        if stored_video is None:
            raise ValueError(f"Video '{video_id}' was not found.")

        video = youtube_service.get_video(db, video_id)
        transcript_record = transcript_service.fetch_for_video(video)

        if transcript_record.transcript_status != "AVAILABLE":
            detail = transcript_record.transcript_detail or transcript_record.transcript_status
            raise SummarizerServiceError(f"Transcript is not available for '{video_id}': {detail}")

        result = generate_summaries([transcript_record], project_id=settings.project_id)
        if result.errors:
            raise SummarizerServiceError("; ".join(result.errors))
        if not result.summaries:
            raise SummarizerServiceError(f"Summary was not generated for '{video_id}'.")

        summary = result.summaries[0]
        self._save_summary_record(db, summary)
        db.commit()
        return summary

    def get_summary(self, db: Session, video_id: str) -> PerVideoSummary:
        summary_row = (
            db.query(SummaryModel)
            .filter(SummaryModel.video_id == video_id)
            .order_by(SummaryModel.created_at.desc())
            .first()
        )
        if summary_row is None:
            raise SummaryNotReadyError(f"Summary for '{video_id}' was not found.")

        try:
            payload = json.loads(summary_row.summary_text)
        except json.JSONDecodeError as exc:
            raise SummarizerServiceError(f"Stored summary for '{video_id}' is invalid JSON.") from exc

        return PerVideoSummary.model_validate(payload)

    @staticmethod
    def _save_summary_record(db: Session, summary: PerVideoSummary) -> SummaryModel:
        payload = summary.model_dump_json()
        existing = (
            db.query(SummaryModel)
            .filter(SummaryModel.video_id == summary.video_id)
            .order_by(SummaryModel.created_at.desc())
            .first()
        )
        if existing is not None:
            existing.summary_text = payload
            return existing

        record = SummaryModel(
            id=uuid4().hex,
            video_id=summary.video_id,
            summary_text=payload,
        )
        db.add(record)
        return record


summarizer_service = SummarizerService()
