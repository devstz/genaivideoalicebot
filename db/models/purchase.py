from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enums import PaymentStatus
from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class Purchase(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    pack_id: Mapped[int] = mapped_column(ForeignKey("packs.id"), nullable=False)

    payment_status: Mapped[PaymentStatus] = mapped_column(String(20), default=PaymentStatus.PENDING, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    external_invoice_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    buyer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="purchases")
    pack: Mapped["Pack"] = relationship(back_populates="purchases")
