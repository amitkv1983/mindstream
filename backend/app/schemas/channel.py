from __future__ import annotations

from pydantic import BaseModel, Field


class ChannelCreateRequest(BaseModel):
    url_or_name: str = Field(..., min_length=1, description="YouTube channel URL, handle, or plain channel name")


class ChannelResponse(BaseModel):
    id: str
    name: str
    url: str
