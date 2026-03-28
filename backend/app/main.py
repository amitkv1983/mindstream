from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine
from app.api.channels import router as channels_router
from app.api.health import router as health_router
from app.api.summaries import router as summaries_router
from app.api.videos import router as videos_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(channels_router)
app.include_router(videos_router)
app.include_router(summaries_router)
