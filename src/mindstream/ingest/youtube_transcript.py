from __future__ import annotations

from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

from mindstream.storage.local_store import raw_dir
from mindstream.storage.models import RawVideoRecord, TranscriptFetchResult, TranscriptSegment, VideoMetadata

TRANSCRIPT_API = YouTubeTranscriptApi()


def save_raw_video_record(record: RawVideoRecord, output_dir: str | None = None, project_id: str = "default") -> str:
    output_path = Path(output_dir) if output_dir else raw_dir(project_id)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{record.metadata.video_id}.json"
    file_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved raw transcript: {file_path.as_posix()}")
    return file_path.as_posix()


def load_raw_video_record(
    video_id: str,
    output_dir: str | None = None,
    project_id: str = "default",
) -> RawVideoRecord | None:
    base_dir = Path(output_dir) if output_dir else raw_dir(project_id)
    file_path = base_dir / f"{video_id}.json"
    if not file_path.exists():
        return None

    try:
        record = RawVideoRecord.model_validate_json(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Cached transcript invalid for: {video_id} -> {exc}")
        return None

    print(f"Loaded cached transcript: {file_path.as_posix()}")
    return record


def _snippet_field(item: object, field: str, default: object) -> object:
    if hasattr(item, field):
        return getattr(item, field)
    if isinstance(item, dict):
        return item.get(field, default)
    return default


def fetch_transcript_for_video(video: VideoMetadata) -> RawVideoRecord:
    print(f"Fetching transcript for video: {video.video_id}")
    try:
        data = TRANSCRIPT_API.fetch(video.video_id)
    except TranscriptsDisabled:
        print(f"Transcript missing for: {video.video_id} -> captions disabled")
        return RawVideoRecord(
            metadata=video,
            transcript_segments=[],
            transcript_status="MISSING",
            transcript_detail="CAPTIONS_DISABLED",
        )
    except NoTranscriptFound:
        print(f"Transcript missing for: {video.video_id} -> no transcript found")
        return RawVideoRecord(
            metadata=video,
            transcript_segments=[],
            transcript_status="MISSING",
            transcript_detail="NO_TRANSCRIPT_FOUND",
        )
    except Exception as exc:
        print(f"Transcript error for: {video.video_id} -> {exc}")
        return RawVideoRecord(
            metadata=video,
            transcript_segments=[],
            transcript_status="ERROR",
            transcript_detail=exc.__class__.__name__,
        )

    segments = [
        TranscriptSegment(
            start=float(_snippet_field(item, "start", 0.0)),
            duration=float(_snippet_field(item, "duration", 0.0)),
            text=str(_snippet_field(item, "text", "")).strip(),
        )
        for item in data
        if str(_snippet_field(item, "text", "")).strip()
    ]

    if not segments:
        print(f"Transcript missing for: {video.video_id} -> empty transcript")
        return RawVideoRecord(
            metadata=video,
            transcript_segments=[],
            transcript_status="MISSING",
            transcript_detail="EMPTY_TRANSCRIPT",
        )

    print(f"Transcript available for: {video.video_id}")
    return RawVideoRecord(
        metadata=video,
        transcript_segments=segments,
        transcript_status="AVAILABLE",
        transcript_detail="TRANSCRIPT_AVAILABLE",
    )


def fetch_transcripts(videos: list[VideoMetadata], project_id: str = "default") -> TranscriptFetchResult:
    result = TranscriptFetchResult()

    for video in videos:
        try:
            cached_record = load_raw_video_record(video.video_id, project_id=project_id)
            if cached_record is not None and cached_record.transcript_status == "AVAILABLE":
                result.fetched_records.append(cached_record)
                continue

            record = fetch_transcript_for_video(video)
            result.fetched_records.append(record)

            if record.transcript_status == "AVAILABLE":
                save_raw_video_record(record, project_id=project_id)
                continue

            if record.transcript_status == "MISSING":
                detail = record.transcript_detail or "UNKNOWN"
                result.missing_transcripts.append(f"{video.video_id}: {detail}")
                continue

            detail = record.transcript_detail or "UNKNOWN_ERROR"
            result.errors.append(f"Transcript error for: {video.video_id} -> {detail}")
        except Exception as exc:
            message = f"Transcript error for: {video.video_id} -> {exc}"
            print(message)
            result.errors.append(message)
            result.fetched_records.append(
                RawVideoRecord(
                    metadata=video,
                    transcript_segments=[],
                    transcript_status="ERROR",
                    transcript_detail=exc.__class__.__name__,
                )
            )

    return result


if __name__ == "__main__":
    test_videos = [
        VideoMetadata(
            video_id="dQw4w9WgXcQ",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
            published_at=None,
        )
    ]

    result = fetch_transcripts(test_videos)

    print("FETCHED RECORDS")
    for record in result.fetched_records:
        print(record.metadata.video_id, record.transcript_status, len(record.transcript_segments))

    print("MISSING")
    print(result.missing_transcripts)

    print("ERRORS")
    print(result.errors)
