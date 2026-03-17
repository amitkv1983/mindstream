from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mindstream.ingest.youtube_discovery import discover_videos
from mindstream.ingest.youtube_transcript import fetch_transcripts
from mindstream.process.summarize_video import generate_summaries
from mindstream.storage.local_store import INDEXED_VIDEOS_PATH


def _load_indexed_videos(index_path: Path = INDEXED_VIDEOS_PATH) -> dict[str, list[str]]:
    if not index_path.exists():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _save_indexed_videos(indexed: dict[str, list[str]], index_path: Path = INDEXED_VIDEOS_PATH) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(indexed, indent=2), encoding="utf-8")


def run_monitoring_cycle(
    sources: list[str],
    max_per_channel: int = 2,
    project_id: str = "default",
    index_path: Path = INDEXED_VIDEOS_PATH,
) -> dict[str, Any]:
    """Discover new videos, skip indexed ones, and run the existing pipeline."""
    discovery = discover_videos(sources, max_per_channel=max_per_channel)
    indexed = _load_indexed_videos(index_path=index_path)
    seen_for_project = set(indexed.get(project_id, []))
    pending_videos = [video for video in discovery.videos if video.video_id not in seen_for_project]

    transcript_result = fetch_transcripts(pending_videos, project_id=project_id)
    summary_result = generate_summaries(transcript_result.fetched_records, project_id=project_id)

    for summary in summary_result.summaries:
        seen_for_project.add(summary.video_id)
    indexed[project_id] = sorted(seen_for_project)
    _save_indexed_videos(indexed, index_path=index_path)

    return {
        "discovery_result": discovery,
        "transcript_result": transcript_result,
        "summary_result": summary_result,
        "processed_videos": sorted(video.video_id for video in pending_videos),
    }


def start_scheduler(
    sources: list[str],
    max_per_channel: int = 2,
    project_id: str = "default",
    hours: int = 6,
):
    """
    Start a lightweight APScheduler job that reuses the existing ingestion flow.

    APScheduler is imported lazily so the rest of Mindstream keeps working even
    when scheduling is not installed or not needed.
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_monitoring_cycle,
        trigger="interval",
        hours=hours,
        kwargs={
            "sources": sources,
            "max_per_channel": max_per_channel,
            "project_id": project_id,
        },
        id=f"mindstream_monitor_{project_id}",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
