"""Mailing service - sends broadcast messages via Telegram Bot."""

from __future__ import annotations

from datetime import datetime, timezone
from logging import getLogger

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import get_settings
from db.models import Mailing
from db.uow import SQLAlchemyUnitOfWork

logger = getLogger(__name__)


async def send_mailing(uow: SQLAlchemyUnitOfWork, mailing: Mailing) -> int:
    """Send mailing to all users in audience. Returns recipient_count."""
    user_ids = await uow.user_repo.list_user_ids_for_audience(
        mailing.audience_filter, include_admins=mailing.include_admins
    )
    settings = get_settings()
    bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    sent = 0
    for uid in user_ids:
        try:
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
