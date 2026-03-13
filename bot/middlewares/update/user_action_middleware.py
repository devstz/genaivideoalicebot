import json
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from db.models import UserAction, User
from db.uow import SQLAlchemyUnitOfWork
from enums import ActionType


class UserActionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Expected to be set by UoWMiddleware and UserMiddleware
        uow: SQLAlchemyUnitOfWork | None = data.get("uow")
        user: User | None = data.get("user")

        if uow and user:
            action_type = None
            payload = {}

            if isinstance(event, Message):
                if event.photo:
                    action_type = ActionType.PHOTO
                elif event.text and event.text.startswith("/"):
                    action_type = ActionType.COMMAND
                    payload["command"] = event.text
                elif event.text:
                    action_type = ActionType.MESSAGE
                    payload["text"] = event.text
            elif isinstance(event, CallbackQuery):
                action_type = ActionType.CALLBACK
                payload["data"] = event.data

            if action_type:
                action = UserAction(
                    user_id=user.user_id,
                    action_type=action_type,
                    payload=payload
                )
                await uow.user_action_repo.add(action)
                # Commit is handled by UoWMiddleware later in the pipeline

        return await handler(event, data)
