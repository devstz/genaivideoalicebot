"""Mailing service - sends broadcast messages via Telegram Bot."""

from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile

from config.settings import get_settings
from db.models import Mailing
from db.uow import SQLAlchemyUnitOfWork

logger = getLogger(__name__)

TELEGRAM_CAPTION_MAX = 1024


def _caption_for_media(text: str | None) -> str | None:
    t = (text or "").strip()
    if not t:
        return None
    if len(t) > TELEGRAM_CAPTION_MAX:
        return t[: TELEGRAM_CAPTION_MAX - 1] + "…"
    return t


def _resolve_attachment_path(mailing: Mailing, media_root: str) -> Path | None:
    if not mailing.attachment_path or not mailing.attachment_type:
        return None
    raw = mailing.attachment_path
    if raw.startswith("/media/"):
        return Path(media_root) / raw[len("/media/") :]
    return Path(media_root) / raw


async def send_mailing(uow: SQLAlchemyUnitOfWork, mailing: Mailing) -> int:
    """Send mailing to all users in audience. Returns recipient_count."""
    user_ids = await uow.user_repo.list_user_ids_for_audience(
        mailing.audience_filter, include_admins=mailing.include_admins
    )
    settings = get_settings()
    bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    media_file: Path | None = _resolve_attachment_path(mailing, settings.MEDIA_ROOT)
    if media_file is not None:
        if not media_file.is_file():
            logger.error("Mailing id=%s attachment not found: %s", mailing.id, media_file)
            mailing.recipient_count = 0
            mailing.status = "failed"
            mailing.sent_at = datetime.now(timezone.utc)
            await uow.mailing_repo.update(mailing)
            await bot.session.close()
            return 0

    sent = 0
    cap = _caption_for_media(mailing.message)
    for uid in user_ids:
        try:
            if media_file is not None and mailing.attachment_type == "photo":
                await bot.send_photo(
                    chat_id=uid,
                    photo=FSInputFile(str(media_file)),
                    caption=cap,
                    parse_mode=ParseMode.HTML if cap else None,
                )
            elif media_file is not None and mailing.attachment_type == "video":
                await bot.send_video(
                    chat_id=uid,
                    video=FSInputFile(str(media_file)),
                    caption=cap,
                    parse_mode=ParseMode.HTML if cap else None,
                )
            else:
                await bot.send_message(chat_id=uid, text=mailing.message)
            sent += 1
        except Exception as e:
            logger.warning("Failed to send mailing to %s: %s", uid, e)
    await bot.session.close()
    mailing.recipient_count = sent
    mailing.status = "sent"
    mailing.sent_at = datetime.now(timezone.utc)
    await uow.mailing_repo.update(mailing)
    return sent
