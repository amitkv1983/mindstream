from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


database_url = settings.database_url
if database_url == "sqlite:///app/data/app.db":
    database_url = "sqlite:////app/data/app.db"

if database_url.endswith("/app/data/app.db"):
    os.makedirs("/app/data", exist_ok=True)

raw_db_path = database_url.replace("sqlite:///", "", 1)
if database_url.startswith("sqlite:////"):
    db_path = Path("/") / raw_db_path.lstrip("/")
else:
    db_path = Path(raw_db_path)
db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
