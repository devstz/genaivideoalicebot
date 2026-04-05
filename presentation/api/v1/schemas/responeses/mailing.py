"""Pydantic schemas for mailing API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class MailingRead(BaseModel):
    id: str
    message: str
    audience_filter: str
    status: str
    recipient_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    attachment_path: Optional[str] = None
    attachment_type: Optional[str] = None


class MailingCreate(BaseModel):
    message: str = ""
    audience: str = "all"
    include_admins: bool = False
    attachment_path: Optional[str] = None
    attachment_type: Optional[str] = Field(
        default=None,
        description="photo or video",
    )

    @model_validator(mode="after")
    def validate_body_and_attachment(self):
        has_text = bool((self.message or "").strip())
        if not has_text and not self.attachment_path:
            raise ValueError("Нужен текст сообщения или вложение (фото/видео).")
        if self.attachment_path:
            if self.attachment_path.startswith("data:"):
                raise ValueError("attachment_path: используйте POST /admin/templates/upload.")
            if self.attachment_type not in ("photo", "video"):
                raise ValueError("attachment_type must be 'photo' or 'video' when attachment_path is set.")
        elif self.attachment_type is not None:
            raise ValueError("attachment_type без attachment_path не допускается.")
        return self


class MailingListResponse(BaseModel):
    items: list[MailingRead]
    total: int


class AudienceStatsResponse(BaseModel):
    count: int
    total: int
    percent: float
