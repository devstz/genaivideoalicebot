"""Mailing repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Mailing


class MailingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, mailing_id: int) -> Optional[Mailing]:
        stmt = select(Mailing).where(Mailing.id == mailing_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(self, limit: int = 50, offset: int = 0) -> tuple[list[Mailing], int]:
        count_stmt = select(func.count()).select_from(Mailing)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one() or 0
        stmt = select(Mailing).order_by(Mailing.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def add(self, mailing: Mailing) -> Mailing:
        self.session.add(mailing)
        await self.session.flush()
        return mailing

    async def update(self, mailing: Mailing) -> Mailing:
        await self.session.flush()
        return mailing
