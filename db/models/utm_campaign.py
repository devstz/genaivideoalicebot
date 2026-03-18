from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from .base import Base, IdPkMixin, ModelHelpersMixin, TimestampMixin


class UtmCampaign(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    __tablename__ = "utm_campaigns"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    utm_source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=expression.true(),
    )

    clicks: Mapped[list["UtmClick"]] = relationship(back_populates="campaign")
    registrations: Mapped[list["UtmRegistration"]] = relationship(back_populates="campaign")
