from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UtmCampaign


class UtmCampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, campaign_id: int) -> Optional[UtmCampaign]:
        stmt = select(UtmCampaign).where(UtmCampaign.id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_start_code(self, start_code: str) -> Optional[UtmCampaign]:
        stmt = select(UtmCampaign).where(UtmCampaign.start_code == start_code)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        is_active: bool | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[UtmCampaign]:
        stmt = select(UtmCampaign)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                UtmCampaign.name.ilike(pattern) | UtmCampaign.start_code.ilike(pattern)
            )
        if is_active is not None:
            stmt = stmt.where(UtmCampaign.is_active == is_active)
        if from_date is not None:
            stmt = stmt.where(UtmCampaign.created_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(UtmCampaign.created_at <= to_date)
        stmt = stmt.order_by(UtmCampaign.created_at.desc(), UtmCampaign.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        stmt = select(func.count(UtmCampaign.id))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                UtmCampaign.name.ilike(pattern) | UtmCampaign.start_code.ilike(pattern)
            )
        if is_active is not None:
            stmt = stmt.where(UtmCampaign.is_active == is_active)
        if from_date is not None:
            stmt = stmt.where(UtmCampaign.created_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(UtmCampaign.created_at <= to_date)
        value = await self.session.scalar(stmt)
        return int(value or 0)

    async def add(self, campaign: UtmCampaign) -> UtmCampaign:
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def update(self, campaign: UtmCampaign, **kwargs: object) -> UtmCampaign:
        for k, v in kwargs.items():
            if hasattr(campaign, k):
                setattr(campaign, k, v)
        await self.session.flush()
        return campaign

    def delete(self, campaign: UtmCampaign) -> None:
        self.session.delete(campaign)
