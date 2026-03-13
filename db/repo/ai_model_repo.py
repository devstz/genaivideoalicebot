from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AiModel


class AiModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_current(self) -> Optional[AiModel]:
        stmt = select(AiModel).where(AiModel.is_current == True)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(self) -> list[AiModel]:
        stmt = select(AiModel)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, ai_model: AiModel) -> AiModel:
        self.session.add(ai_model)
        await self.session.flush()
        return ai_model
