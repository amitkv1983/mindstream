from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.schemas.summary import SummaryResponse, SummaryTriggerResponse
from app.services.summarizer_service import SummarizerServiceError, summarizer_service


router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/{video_id}/summarize", response_model=SummaryTriggerResponse)
def summarize_video(video_id: str, db: Session = Depends(get_db)) -> SummaryTriggerResponse:
    try:
        summary = summarizer_service.summarize_video(db, video_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SummarizerServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SummaryTriggerResponse(
        status="completed",
        summary=SummaryResponse.model_validate(summary),
    )
