from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Purchase


class PurchaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_user(self, user_id: int) -> list[Purchase]:
        stmt = select(Purchase).where(Purchase.user_id == user_id).order_by(Purchase.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, purchase: Purchase) -> Purchase:
        self.session.add(purchase)
        await self.session.flush()
        return purchase
