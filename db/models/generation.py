from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enums import GenerationStatus
from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Generation(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("templates.id"), nullable=True)

    status: Mapped[GenerationStatus] = mapped_column(String(20), default=GenerationStatus.PENDING, nullable=False)

    input_photo_path: Mapped[str] = mapped_column(String(255), nullable=False)
    user_prompt: Mapped[Optional[str]] = mapped_column(Text)
    final_prompt: Mapped[Optional[str]] = mapped_column(Text)
    external_task_id: Mapped[Optional[str]] = mapped_column(String(100))
    result_video_path: Mapped[Optional[str]] = mapped_column(String(255))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="generations")
    template: Mapped[Optional["Template"]] = relationship(back_populates="generations")
