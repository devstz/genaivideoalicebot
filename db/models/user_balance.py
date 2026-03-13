from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class UserBalance(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    generations_remaining: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)

    user: Mapped["User"] = relationship(back_populates="balance")
