from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserAction


class UserActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, action: UserAction) -> UserAction:
        self.session.add(action)
        await self.session.flush()
        return action
