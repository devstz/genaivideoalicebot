from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models import User

logger = getLogger(__name__)


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_admin_login(self, admin_login: str) -> Optional[User]:
        stmt = select(User).where(User.admin_login == admin_login)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def count_users(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
    ) -> int:
        stmt = select(func.count()).select_from(User)

        conditions = []
        if is_superuser is not None:
            conditions.append(User.is_superuser == is_superuser)
        if username_like:
            conditions.append(User.username.ilike(f"%{username_like}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(
        self,
        *,
        is_superuser: Optional[bool] = None,
        username_like: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        stmt = select(User)

        conditions = []
        if is_superuser is not None:
            conditions.append(User.is_superuser == is_superuser)
        if username_like:
            conditions.append(User.username.ilike(f"%{username_like}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    # Aliases used by UserService
    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.get(user_id)

    async def create(self, user: User) -> User:
        return await self.add(user)

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        stmt = select(User).where(User.referral_code == code)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get(user_id)
        if user is not None:
            await self.session.delete(user)
            await self.session.flush()

    async def count_for_audience(self, audience: str, *, include_admins: bool = False) -> int:
        """Count users for mailing audience filter."""
        from datetime import datetime, timezone, timedelta
        from db.models import UserAction

        if audience == "all":
            stmt = select(func.count()).select_from(User)
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)
        elif audience == "new_7d":
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            stmt = select(func.count()).select_from(User).where(
                User.created_at >= cutoff
            )
            if not include_admins:
                stmt = stmt.where(not_admin)
        elif audience == "active_24h":
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            subq = (
                select(UserAction.user_id)
                .where(UserAction.created_at >= cutoff)
                .distinct()
            )
            stmt = select(func.count()).select_from(User).where(User.user_id.in_(subq))
            if not include_admins:
                stmt = stmt.where(not_admin)
        elif audience == "inactive_1d":
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            active_subq = select(UserAction.user_id).where(UserAction.created_at >= cutoff).distinct()
            stmt = select(func.count()).select_from(User).where(User.user_id.not_in(active_subq))
            if not include_admins:
                stmt = stmt.where(not_admin)
        else:
            stmt = select(func.count()).select_from(User)
            if not include_admins:
                stmt = stmt.where(not_admin)

        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def list_user_ids_for_audience(self, audience: str, *, include_admins: bool = False) -> list[int]:
        """Get user_ids for mailing by audience filter."""
        from datetime import datetime, timezone, timedelta
        from db.models import UserAction

        if audience == "all":
            stmt = select(User.user_id)
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)
        elif audience == "new_7d":
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            stmt = select(User.user_id).where(User.created_at >= cutoff)
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)
        elif audience == "active_24h":
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            subq = select(UserAction.user_id).where(UserAction.created_at >= cutoff).distinct()
            stmt = select(User.user_id).where(User.user_id.in_(subq))
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)
        elif audience == "inactive_1d":
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            active_subq = select(UserAction.user_id).where(UserAction.created_at >= cutoff).distinct()
            stmt = select(User.user_id).where(User.user_id.not_in(active_subq))
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)
        else:
            stmt = select(User.user_id)
            if not include_admins:
                stmt = stmt.where(User.is_superuser == False)

        result = await self.session.execute(stmt)
        return [r[0] for r in result.all()]
