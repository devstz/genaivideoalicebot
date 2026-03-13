from contextlib import suppress
import asyncio
from logging import getLogger

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logger = getLogger(__name__)


def _resolve_message(event: CallbackQuery | Message) -> Message:
    """Извлекает объект Message из события."""
    if isinstance(event, CallbackQuery):
        msg = event.message
    elif isinstance(event, Message):
        msg = event
    else:
        raise TypeError(f"Expected CallbackQuery or Message, got {type(event).__name__}")
    if not isinstance(msg, Message):
        raise TypeError(f"Expected Message, got {type(msg).__name__}")
    return msg


async def edit_message(
        event: CallbackQuery | Message,
        text: str | None = None,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | None = None,
        photo=None, **kwargs
    ):
    message = _resolve_message(event)

    try:
        if photo:
            media = InputMediaPhoto(media=photo, caption=text)
            return await message.edit_media(media, reply_markup=reply_markup)  # type: ignore
        try:
            return await message.edit_text(text=text, reply_markup=reply_markup, **kwargs)  # type: ignore
        except Exception as e:
            if 'is not modified' in str(e):
                return
            with suppress(Exception):
                await message.delete()
            return await message.answer(text=text, reply_markup=reply_markup, **kwargs)  # type: ignore
    except TelegramBadRequest as e:
        if 'message is not modified' in str(e):
            return

    with suppress(Exception):
        if isinstance(event, CallbackQuery):
            await message.delete()
    if photo:
        with suppress(Exception):
            return await message.answer_photo(photo=photo, caption=text, reply_markup=reply_markup, **kwargs)
    return await message.answer(text=text, reply_markup=reply_markup, **kwargs)  # type: ignore


async def _delete_message_with_sleep(event: CallbackQuery | Message, sleep: int = 1):
    with suppress(Exception):
        await asyncio.sleep(sleep)
        message = _resolve_message(event)
        await message.delete()


async def delete_message_with_sleep(event: CallbackQuery | Message, sleep: int = 1):
    asyncio.create_task(_delete_message_with_sleep(event, sleep))
