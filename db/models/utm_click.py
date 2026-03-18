from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdPkMixin, ModelHelpersMixin, TimestampMixin


class UtmClick(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    __tablename__ = "utm_clicks"
    __table_args__ = (
        UniqueConstraint("utm_campaign_id", "user_id", name="uq_utm_clicks_utm_campaign_user"),
    )

    utm_campaign_id: Mapped[int] = mapped_column(ForeignKey("utm_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    campaign: Mapped["UtmCampaign"] = relationship(back_populates="clicks")
    user: Mapped["User"] = relationship()
