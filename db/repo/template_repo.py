from __future__ import annotations

from typing import Optional

from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Template
from enums import TemplateStatus


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, template_id: int) -> Optional[Template]:
        stmt = select(Template).where(Template.id == template_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_active(self) -> list[Template]:
        stmt = select(Template).where(Template.status == TemplateStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_category(self, category: str) -> list[Template]:
        stmt = select(Template).where(Template.category == category, Template.status == TemplateStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[Template]:
        stmt = select(Template).order_by(Template.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_distinct_categories(self) -> list[str]:
        from sqlalchemy import distinct
        stmt = select(distinct(Template.category)).where(Template.category.isnot(None)).order_by(Template.category)
        result = await self.session.execute(stmt)
        return [r[0] for r in result.scalars().all() if r[0]]

    async def add(self, template: Template) -> Template:
        self.session.add(template)
        await self.session.flush()
        return template

    def delete(self, template: Template) -> None:
        self.session.delete(template)
