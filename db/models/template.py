from __future__ import annotations

from typing import Optional

from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enums import TemplateStatus
from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Template(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    preview_image_path: Mapped[Optional[str]] = mapped_column(String(255))
    preview_video_path: Mapped[Optional[str]] = mapped_column(String(255))
    
    base_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text)
    
    status: Mapped[TemplateStatus] = mapped_column(String(20), default=TemplateStatus.HIDDEN, nullable=False)
    
    ai_model_id: Mapped[int] = mapped_column(ForeignKey("aimodels.id"), nullable=False)
    ai_model: Mapped["AiModel"] = relationship(back_populates="templates")

    generations: Mapped[list["Generation"]] = relationship(back_populates="template")
