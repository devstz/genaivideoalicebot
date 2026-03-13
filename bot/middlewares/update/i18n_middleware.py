"""
i18n middleware — resolves the user's language and injects the locale module
into handler data as `i18n`.

Usage in handler:
    async def cmd_start(self, message: Message, i18n, **kw):
        await message.answer(i18n.WELCOME_FIRST)
"""
from logging import getLogger
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from bot.locales import ru, en

logger = getLogger(__name__)

SUPPORTED_LANGS = {"ru": ru, "en": en}
DEFAULT_LANG = "ru"


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: User | None = data.get("event_from_user")

        lang = DEFAULT_LANG
        if tg_user and tg_user.language_code:
            code = tg_user.language_code.lower().split("-")[0]  # "en-US" → "en"
            if code in SUPPORTED_LANGS:
                lang = code

        data["i18n"] = SUPPORTED_LANGS[lang]
        data["lang"] = lang

        return await handler(event, data)
