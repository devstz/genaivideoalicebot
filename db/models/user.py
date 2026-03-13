from __future__ import annotations
import uuid
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy import text

from .base import Base, TimestampMixin, VersionedMixin, ModelHelpersMixin


class User(Base, TimestampMixin, ModelHelpersMixin):
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
    )

    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
    )

    referral_code: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, index=True,
        default=lambda: uuid.uuid4().hex[:12]
    )
    has_accepted_agreement: Mapped[bool] = mapped_column(Boolean, default=False, server_default=expression.false(), nullable=False)

    balance: Mapped["UserBalance"] = relationship(back_populates="user", uselist=False)
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="user")
    generations: Mapped[list["Generation"]] = relationship(back_populates="user")
    actions: Mapped[list["UserAction"]] = relationship(back_populates="user")
    referrals_made: Mapped[list["Referral"]] = relationship(
        foreign_keys="[Referral.referrer_id]", 
        back_populates="referrer"
    )
