import asyncio
from collections import defaultdict
from logging import getLogger
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User, Update
from aiogram.utils.deep_linking import decode_payload

from db.models import User as UserDB
from db.models import Referral
from db.uow import SQLAlchemyUnitOfWork
from services.utm_service import UtmService

logger = getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _extract_start_payload(self, event: TelegramObject) -> str | None:
        """Extract decoded /start deep link payload."""
        if not isinstance(event, Update) or not event.message or not event.message.text:
            return None
        text = event.message.text
        if not text.startswith("/start "):
            return None
        raw_payload = text.split(" ", 1)[1]
        try:
            decoded = decode_payload(raw_payload)
        except Exception:
            decoded = raw_payload
        return decoded

    def _extract_referral_code(self, event: TelegramObject) -> str | None:
        """Extract referral code from /start deep link payload."""
        decoded = self._extract_start_payload(event)
        if not decoded:
            return None

        # Support both "ref_CODE" and just raw code
        if decoded.startswith("ref_"):
            return decoded[4:]
        return decoded

    def _extract_utm_start_code(self, event: TelegramObject) -> str | None:
        payload = self._extract_start_payload(event)
        if not payload:
            return None
        if payload.startswith("auth_") or payload.startswith("ref_"):
            return None
        if payload.startswith("utm_"):
            return payload[4:]
        return payload

    async def _apply_referral(self, uow: SQLAlchemyUnitOfWork, new_user: UserDB, referral_code: str, bot: Bot) -> None:
        """Create referral pair and give +1 gen to referrer."""
        referrer = await uow.user_repo.get_by_referral_code(referral_code)
        if not referrer:
            logger.info("Referral skipped: code '%s' not found in DB", referral_code)
            return
        if referrer.user_id == new_user.user_id:
            logger.info("Referral skipped: user %s tried to use own code", new_user.user_id)
            return

        existing = await uow.referral_repo.get_by_referred(new_user.user_id)
        if existing:
            logger.info("Referral skipped: user %s already referred", new_user.user_id)
            return

        referral = Referral(referrer_id=referrer.user_id, referred_id=new_user.user_id, bonus_applied=True)
        await uow.referral_repo.add(referral)
        await uow.user_balance_repo.add_generations(referrer.user_id, 1)
        logger.info("Referral applied: user %s -> referrer %s (+1 gen)", new_user.user_id, referrer.user_id)

        # Notify referrer about the bonus
        try:
            await bot.send_message(
                referrer.user_id,
                "По вашей ссылке запустили бота! Вам доступна 1 бесплатная генерация! 🎁",
            )
        except Exception:
            logger.warning("Failed to notify referrer %s about referral bonus", referrer.user_id)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        uow: SQLAlchemyUnitOfWork = data['uow']
        tg_user: User = data['event_from_user']

        async with self._locks[tg_user.id]:
            db_user = await uow.user_repo.get(tg_user.id)
            is_new_user = False

            if db_user is None:
                try:
                    db_user = await uow.user_repo.add(
                        UserDB(
                            user_id=tg_user.id,
                            username=tg_user.username,
                            first_name=tg_user.first_name,
                            last_name=tg_user.last_name,
                            full_name=tg_user.full_name,
                            language_code=tg_user.language_code,
                        )
                    )
                    is_new_user = True
                    await uow.user_balance_repo.get_or_create(tg_user.id)

                    # Process referral right after user creation
                    ref_code = self._extract_referral_code(event)
                    if ref_code:
                        await self._apply_referral(uow, db_user, ref_code, data["bot"])

                except Exception:
                    logger.exception("Error creating user %s, retrying get", tg_user.id)
                    await uow.session.rollback()
                    await uow.session.begin()
                    db_user = await uow.user_repo.get(tg_user.id)
                    if db_user is None:
                        logger.error("Failed to get or create user %s", tg_user.id)
                        return
            else:
                changed = False
                if db_user.username != tg_user.username:
                    logger.info("User %s changed username: %s -> %s", tg_user.id, db_user.username, tg_user.username)
                    db_user.username = tg_user.username
                    changed = True
                if db_user.first_name != tg_user.first_name:
                    logger.info("User %s changed first_name: %s -> %s", tg_user.id, db_user.first_name, tg_user.first_name)
                    db_user.first_name = tg_user.first_name
                    changed = True
                if db_user.last_name != tg_user.last_name:
                    logger.info("User %s changed last_name: %s -> %s", tg_user.id, db_user.last_name, tg_user.last_name)
                    db_user.last_name = tg_user.last_name
                    changed = True
                if db_user.language_code != tg_user.language_code:
                    db_user.language_code = tg_user.language_code
                    changed = True
                if db_user.full_name != tg_user.full_name:
                    db_user.full_name = tg_user.full_name
                    changed = True
                if changed:
                    await uow.user_repo.update(db_user)

            utm_start_code = self._extract_utm_start_code(event)
            if utm_start_code:
                campaign = await UtmService.resolve_campaign_by_start_code(uow, start_code=utm_start_code)
                if campaign:
                    if is_new_user:
                        await UtmService.track_registration_if_new(
                            uow,
                            campaign_id=campaign.id,
                            user_id=db_user.user_id,
                        )
                    await UtmService.track_click_if_new(
                        uow,
                        campaign_id=campaign.id,
                        user_id=db_user.user_id,
                    )

            data.update(user=db_user)

        return await handler(event, data)
