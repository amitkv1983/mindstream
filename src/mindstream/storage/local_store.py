from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mindstream.storage.models import PerVideoSummary, RawVideoRecord


RAW_DIR = Path("data/raw")
PER_VIDEO_DIR = Path("data/per_video")
REPORTS_DIR = Path("data/reports")


def ensure_data_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PER_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save_raw_record(record: RawVideoRecord) -> Path:
    path = RAW_DIR / f"{record.metadata.video_id}.json"
    path.write_text(json.dumps(record.model_dump(), indent=2), encoding="utf-8")
    return path


def save_per_video_summary(summary: PerVideoSummary) -> Path:
    path = PER_VIDEO_DIR / f"{summary.video_id}.json"
    path.write_text(json.dumps(summary.model_dump(), indent=2), encoding="utf-8")
    return path


def save_report(report: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORTS_DIR / f"{ts}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
