from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class Settings:
    def __init__(self) -> None:
        default_db_path = (BACKEND_DIR / "data" / "app.db").resolve().as_posix()
        self.app_name = os.getenv("APP_NAME", "Mindstream Backend")
        self.app_version = os.getenv("APP_VERSION", "0.1.0")
        self.project_id = os.getenv("PROJECT_ID", "default")
        self.database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")


settings = Settings()
