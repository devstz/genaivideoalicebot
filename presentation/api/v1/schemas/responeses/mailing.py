"""Pydantic schemas for mailing API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MailingRead(BaseModel):
    id: str
    message: str
    audience_filter: str
    status: str
    recipient_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None


class MailingCreate(BaseModel):
    message: str
    audience: str = "all"
    include_admins: bool = False


class MailingListResponse(BaseModel):
    items: list[MailingRead]
    total: int


class AudienceStatsResponse(BaseModel):
    count: int
    total: int
    percent: float
