from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_referred(self, referred_id: int) -> Referral | None:
        stmt = select(Referral).where(Referral.referred_id == referred_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_by_referrer(self, referrer_id: int) -> int:
        stmt = select(func.count()).select_from(Referral).where(Referral.referrer_id == referrer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, referral: Referral) -> Referral:
        self.session.add(referral)
        await self.session.flush()
        return referral
