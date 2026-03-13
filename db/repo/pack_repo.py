from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Pack


class PackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, pack_id: int) -> Optional[Pack]:
        stmt = select(Pack).where(Pack.id == pack_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_active(self) -> list[Pack]:
        stmt = select(Pack).where(Pack.is_active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[Pack]:
        stmt = select(Pack).order_by(Pack.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, pack: Pack) -> Pack:
        self.session.add(pack)
        await self.session.flush()
        return pack

    async def update(self, pack: Pack, **kwargs: object) -> Pack:
        for k, v in kwargs.items():
            if hasattr(pack, k):
                setattr(pack, k, v)
        await self.session.flush()
        return pack

    def delete(self, pack: Pack) -> None:
        self.session.delete(pack)
