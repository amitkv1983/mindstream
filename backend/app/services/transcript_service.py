from __future__ import annotations

from mindstream.ingest.youtube_transcript import fetch_transcripts
from mindstream.storage.models import RawVideoRecord, VideoMetadata

from app.core.config import settings


class TranscriptService:
    def fetch_for_video(self, video: VideoMetadata) -> RawVideoRecord:
        result = fetch_transcripts([video], project_id=settings.project_id)
        if result.fetched_records:
            return result.fetched_records[0]
        raise RuntimeError(f"Transcript pipeline returned no record for video '{video.video_id}'.")


transcript_service = TranscriptService()
