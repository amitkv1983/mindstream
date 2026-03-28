from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.schemas.summary import SummaryResponse
from app.services.summarizer_service import SummaryNotReadyError, summarizer_service


router = APIRouter(prefix="/videos", tags=["summaries"])


@router.get("/{video_id}/summary", response_model=SummaryResponse)
def get_video_summary(video_id: str, db: Session = Depends(get_db)) -> SummaryResponse:
    try:
        summary = summarizer_service.get_summary(db, video_id)
    except SummaryNotReadyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SummaryResponse.model_validate(summary)
