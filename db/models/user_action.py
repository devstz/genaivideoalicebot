from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from enums import ActionType
from .base import Base, TimestampMixin, ModelHelpersMixin, IdPkMixin


class UserAction(Base, TimestampMixin, ModelHelpersMixin, IdPkMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    action_type: Mapped[ActionType] = mapped_column(String(20), nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
    )

    user: Mapped["User"] = relationship(back_populates="actions")
