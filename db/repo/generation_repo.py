from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Generation
from enums import GenerationStatus


class GenerationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, generation_id: int) -> Optional[Generation]:
        stmt = select(Generation).where(Generation.id == generation_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_user(self, user_id: int, limit: int = 10) -> list[Generation]:
        stmt = select(Generation).where(Generation.user_id == user_id).order_by(Generation.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_admin(
        self,
        *,
        limit: int = 200,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> tuple[list[Generation], int]:
        conditions = []
        if status:
            try:
                status_enum = GenerationStatus(status)
                conditions.append(Generation.status == status_enum)
            except ValueError:
                pass

        base_stmt = select(Generation)
        if conditions:
            base_stmt = base_stmt.where(*conditions)

        count_stmt = select(func.count()).select_from(Generation)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one() or 0

        stmt = base_stmt.order_by(Generation.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def add(self, generation: Generation) -> Generation:
        self.session.add(generation)
        await self.session.flush()
        return generation

    async def update(self, generation: Generation) -> Generation:
        await self.session.flush()
        return generation
