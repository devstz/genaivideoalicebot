from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from db.models import GlobalSetting


class GlobalSettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        stmt = select(GlobalSetting.value).where(GlobalSetting.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> dict[str, str]:
        stmt = select(GlobalSetting.key, GlobalSetting.value)
        result = await self.session.execute(stmt)
        return dict(result.all()) # type: ignore

    async def set(self, key: str, value: str) -> None:
        stmt = insert(GlobalSetting).values(key=key, value=value).on_conflict_do_update(
            index_elements=['key'],
            set_={'value': value}
        )
        await self.session.execute(stmt)
        await self.session.flush()
