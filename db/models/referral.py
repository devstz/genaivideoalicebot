from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Referral(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    bonus_applied: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    referrer: Mapped["User"] = relationship(foreign_keys=[referrer_id], back_populates="referrals_made")
    referred: Mapped["User"] = relationship(foreign_keys=[referred_id])
