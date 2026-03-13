from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.uow import SQLAlchemyUnitOfWork
from services.user_service import UserService
from services.template_service import TemplateService
from services.pack_service import PackService
from services.generation_service import GenerationService


class ServiceMiddleware(BaseMiddleware):
    """
    Injects service instances into handler data so that routers can use them
    via aiogram's built-in DI (keyword arguments in handlers).
    Must be registered AFTER UoWMiddleware so that `uow` is available.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        uow: SQLAlchemyUnitOfWork | None = data.get("uow")

        if uow:
            data["user_service"] = UserService(uow)
            data["template_service"] = TemplateService(uow)
            data["pack_service"] = PackService(uow)
            data["generation_service"] = GenerationService(uow)

        return await handler(event, data)
