from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Pack(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    generations_count: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="payments", server_default="payments", nullable=False)
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="pack")
