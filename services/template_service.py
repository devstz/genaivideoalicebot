from typing import Optional

from db.models import Template
from db.uow import SQLAlchemyUnitOfWork


class TemplateService:
    def __init__(self, uow: SQLAlchemyUnitOfWork) -> None:
        self.uow = uow

    async def get_active_templates(self) -> list[Template]:
        return await self.uow.template_repo.list_active_by_type("preset")

    async def get_active_postcards(self) -> list[Template]:
        return await self.uow.template_repo.list_active_by_type("postcard")

    async def get_template(self, template_id: int) -> Optional[Template]:
        return await self.uow.template_repo.get(template_id)
