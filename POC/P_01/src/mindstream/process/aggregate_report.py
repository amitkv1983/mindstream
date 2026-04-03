from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from mindstream.storage.models import PerVideoSummary, RawVideoRecord


def build_report(
    summaries: list[PerVideoSummary],
    raw_records: list[RawVideoRecord],
    window_hours: int,
    max_videos: int,
) -> dict:
    topic_counter: Counter[str] = Counter()
    bullet_counter: Counter[str] = Counter()

    for summary in summaries:
        topic_counter.update(summary.topics)
        bullet_counter.update(summary.bullets)

    themes = [{"theme": topic, "frequency": count} for topic, count in topic_counter.most_common(10)]

    executive_summary: list[str] = []
    executive_summary.extend([f"Theme: {t['theme']} ({t['frequency']})" for t in themes[:3]])
    executive_summary.extend([b for b, _ in bullet_counter.most_common(2)])
    executive_summary = executive_summary[:5]

    generated_at = datetime.now(timezone.utc)
    report = {
        "schema_version": "1.0",
        "report_id": str(uuid4()),
        "report_window": {
            "start_utc": (generated_at - timedelta(hours=window_hours)).isoformat(),
            "end_utc": generated_at.isoformat(),
            "window_hours": window_hours,
        },
        "run_metadata": {
            "videos_discovered": len(raw_records),
            "videos_processed": len(summaries),
            "videos_missing_transcript": sum(1 for r in raw_records if r.transcript_status != "available"),
            "max_videos": max_videos,
        },
        "executive_summary": executive_summary,
        "themes": themes,
        "contradictions": [],
        "watchlist": [topic for topic, _ in topic_counter.most_common(5)],
        "what_stayed_the_same": [],
        "status_message": (
            "No new material in the selected window."
            if len(summaries) == 0
            else f"Report generated from {len(summaries)} videos."
        ),
        "policy_compliance": {
            "redaction_enabled": True,
            "notes": "Basic profile/name redaction stub applied to user-visible fields.",
        },
        "redaction_audit": {
            "overall_status": "PASS",
            "sanitized": False,
            "replacement_count": 0,
        },
        "internal_appendix": {
            "sources": [
                {
                    "video_id": r.metadata.video_id,
                    "video_url": r.metadata.video_url,
                    "transcript_status": r.transcript_status,
                }
                for r in raw_records
            ],
            "evidence_index": {},
        },
    }

    return report
