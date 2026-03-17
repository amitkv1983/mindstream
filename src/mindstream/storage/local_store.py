from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mindstream.storage.models import PerVideoSummary, RawVideoRecord


DATA_DIR = Path("data")
PROJECTS_DIR = DATA_DIR / "projects"
RAW_DIR = DATA_DIR / "raw"
PER_VIDEO_DIR = DATA_DIR / "per_video"
REPORTS_DIR = DATA_DIR / "reports"
INDEXED_VIDEOS_PATH = DATA_DIR / "indexed_videos.json"


def project_dir(project_id: str = "default") -> Path:
    safe_project_id = (project_id or "default").strip() or "default"
    return PROJECTS_DIR / safe_project_id


def raw_dir(project_id: str = "default") -> Path:
    return project_dir(project_id) / "raw"


def per_video_dir(project_id: str = "default") -> Path:
    return project_dir(project_id) / "per_video"


def reports_dir(project_id: str = "default") -> Path:
    return project_dir(project_id) / "reports"


def ensure_data_dirs(project_id: str = "default") -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PER_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir(project_id).mkdir(parents=True, exist_ok=True)
    per_video_dir(project_id).mkdir(parents=True, exist_ok=True)
    reports_dir(project_id).mkdir(parents=True, exist_ok=True)


def save_raw_record(record: RawVideoRecord, project_id: str = "default") -> Path:
    path = raw_dir(project_id) / f"{record.metadata.video_id}.json"
    path.write_text(json.dumps(record.model_dump(), indent=2), encoding="utf-8")
    return path


def save_per_video_summary(summary: PerVideoSummary, project_id: str = "default") -> Path:
    path = per_video_dir(project_id) / f"{summary.video_id}.json"
    path.write_text(json.dumps(summary.model_dump(), indent=2), encoding="utf-8")
    return path


def save_report(report: dict, project_id: str = "default") -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = reports_dir(project_id) / f"{ts}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
