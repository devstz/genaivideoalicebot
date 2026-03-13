from __future__ import annotations

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class AiModel(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    templates: Mapped[list["Template"]] = relationship(back_populates="ai_model")
