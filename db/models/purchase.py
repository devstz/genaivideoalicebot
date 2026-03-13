from __future__ import annotations

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enums import PaymentStatus
from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Purchase(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    pack_id: Mapped[int] = mapped_column(ForeignKey("packs.id"), nullable=False)
    
    payment_status: Mapped[PaymentStatus] = mapped_column(String(20), default=PaymentStatus.PENDING, nullable=False)

    user: Mapped["User"] = relationship(back_populates="purchases")
    pack: Mapped["Pack"] = relationship(back_populates="purchases")
