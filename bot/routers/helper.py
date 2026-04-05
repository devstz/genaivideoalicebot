from contextlib import suppress
import asyncio
from logging import getLogger
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAnimation,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from config import get_settings

logger = getLogger(__name__)


def _resolve_media(value):
    """If value looks like a local file path, wrap it in FSInputFile."""
    if not isinstance(value, str):
        return value
    if value.startswith(("http://", "https://")):
        return value
    if "/" in value or value.endswith((".mp4", ".jpg", ".jpeg", ".png", ".gif", ".webm")):
        settings = get_settings()
        # Try MEDIA_ROOT/value
        full_path = Path(settings.MEDIA_ROOT) / value
        if full_path.exists():
            logger.info("_resolve_media: found %s -> FSInputFile(%s)", value, full_path)
            return str(full_path)
        # Try as-is
        p = Path(value)
        if p.exists():
            logger.info("_resolve_media: found as-is %s", value)
            return str(p)
        # Try stripping /media/ prefix
        if value.startswith("/media/"):
            stripped = Path(settings.MEDIA_ROOT) / value[7:]
            if stripped.exists():
                logger.info("_resolve_media: found stripped %s -> %s", value, stripped)
                return str(stripped)
        logger.warning("_resolve_media: file not found: %s (tried %s)", value, full_path)
    return value


def _make_fsinput(path_or_id):
    """Create FSInputFile from a resolved local path, or return as-is if it's a file_id/URL."""
    if isinstance(path_or_id, str) and not path_or_id.startswith(("http://", "https://")) and Path(path_or_id).exists():
        return FSInputFile(path_or_id)
    return path_or_id


def _resolve_message(event: CallbackQuery | Message) -> Message:
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
        photo=None, video=None, animation=None, **kwargs
    ):
    message = _resolve_message(event)

    # Resolve local file paths
    if video:
        video = _resolve_media(video)
    if photo:
        photo = _resolve_media(photo)
    if animation:
        animation = _resolve_media(animation)

    # Strategy: try edit_media first; if fails (e.g. text->media), delete + send new
    has_media = video or photo or animation

    if has_media:
        # Try editing existing media message
        try:
            if video:
                media = InputMediaVideo(media=_make_fsinput(video), caption=text)
            elif animation:
                media = InputMediaAnimation(media=_make_fsinput(animation), caption=text)
            else:
                media = InputMediaPhoto(media=_make_fsinput(photo), caption=text)
            return await message.edit_media(media, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if 'message is not modified' in str(e):
                return
            logger.info("edit_media failed (%s), falling back to delete+send", e)
        except Exception as e:
            logger.info("edit_media failed (%s), falling back to delete+send", e)

        # Fallback: delete old message and send new one with media
        try:
            await message.delete()
        except Exception:
            pass

        try:
            if video:
                return await message.answer_video(video=_make_fsinput(video), caption=text, reply_markup=reply_markup, **kwargs)
            elif animation:
                return await message.answer_animation(animation=_make_fsinput(animation), caption=text, reply_markup=reply_markup, **kwargs)
            else:
                return await message.answer_photo(photo=_make_fsinput(photo), caption=text, reply_markup=reply_markup, **kwargs)
        except Exception as e:
            logger.error("Failed to send media fallback: %s", e)
            return await message.answer(text=text or "", reply_markup=reply_markup, **kwargs)

    # No media — just edit text
    try:
        return await message.edit_text(text=text, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        if 'is not modified' in str(e):
            return
        logger.info("edit_text failed (%s), falling back to delete+answer", e)
        with suppress(Exception):
            await message.delete()
        return await message.answer(text=text or "", reply_markup=reply_markup, **kwargs)


async def _delete_message_with_sleep(event: CallbackQuery | Message, sleep: int = 1):
    with suppress(Exception):
        await asyncio.sleep(sleep)
        message = _resolve_message(event)
        await message.delete()


async def delete_message_with_sleep(event: CallbackQuery | Message, sleep: int = 1):
    asyncio.create_task(_delete_message_with_sleep(event, sleep))
