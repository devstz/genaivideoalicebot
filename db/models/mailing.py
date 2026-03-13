"""Mailing model for newsletter broadcasts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Mailing(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    message: Mapped[str] = mapped_column(Text, nullable=False)
    audience_filter: Mapped[str] = mapped_column(String(30), default="all", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    recipient_count: Mapped[int] = mapped_column(default=0, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    include_admins: Mapped[bool] = mapped_column(default=False, nullable=False)
