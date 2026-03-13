"""Pydantic schemas for generation logs API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GenerationLogRead(BaseModel):
    id: str
    created_at: datetime
    source_image_url: str
    user_prompt: Optional[str] = None
    result_video_url: Optional[str] = None
    status: str
    error_message: Optional[str] = None


class GenerationLogListResponse(BaseModel):
    items: list[GenerationLogRead]
    total: int
