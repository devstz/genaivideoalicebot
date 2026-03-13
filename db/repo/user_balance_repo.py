from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserBalance


class UserBalanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user(self, user_id: int) -> Optional[UserBalance]:
        stmt = select(UserBalance).where(UserBalance.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create(self, user_id: int) -> UserBalance:
        balance = await self.get_by_user(user_id)
        if balance is None:
            balance = UserBalance(user_id=user_id, generations_remaining=0)
            self.session.add(balance)
            await self.session.flush()
        return balance

    async def add_generations(self, user_id: int, count: int) -> UserBalance:
        balance = await self.get_or_create(user_id)
        stmt = update(UserBalance).where(UserBalance.user_id == user_id).values(
            generations_remaining=UserBalance.generations_remaining + count
        ).returning(UserBalance)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalars().first() # type: ignore

    async def subtract_generations(self, user_id: int, count: int) -> UserBalance:
        return await self.add_generations(user_id, -count)
