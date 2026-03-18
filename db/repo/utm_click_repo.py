from __future__ import annotations

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UtmClick


class UtmClickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_for_user(self, *, campaign_id: int, user_id: int) -> bool:
        stmt = select(
            exists().where(
                and_(UtmClick.utm_campaign_id == campaign_id, UtmClick.user_id == user_id)
            )
        )
        value = await self.session.scalar(stmt)
        return bool(value)

    async def add(self, click: UtmClick) -> UtmClick:
        self.session.add(click)
        await self.session.flush()
        return click
