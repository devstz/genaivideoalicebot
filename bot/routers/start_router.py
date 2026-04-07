import logging
from aiogram import F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import main_menu_kb, agreement_kb, auth_confirm_kb
from bot.keyboards.callback_data.private import MainMenuCD, ConfirmCD
from services.user_service import UserService
from services.auth.cache_auth_repo import CacheAuthRepository
from presentation.api.v1.routers.admin.auth import _auth_repo
from db.models import User
from config import get_settings


logger = logging.getLogger(__name__)


class StartRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.message.register(self.cmd_start_auth, CommandStart(deep_link=True, magic=F.args.startswith('auth_')))
        self.message.register(self.cmd_start, CommandStart())
        self.callback_query.register(self.accept_agreement, MainMenuCD.filter(F.action == "accept_agreement"))
        self.callback_query.register(self.auth_approve, ConfirmCD.filter(F.action.startswith("auth_approve_")))
        self.callback_query.register(self.auth_reject, ConfirmCD.filter(F.action.startswith("auth_reject_")))

    async def cmd_start_auth(self, message: Message, command: CommandObject, user: User) -> None:
        if not user.is_superuser:
            # Ignore ordinary users trying to auth as admin
            return

        token = command.args.replace('auth_', '')
        session = await _auth_repo.get_session(token)
        if not session:
            await message.answer("❌ Код авторизации истек или недействителен.")
            return

        if session.get("session_type") == "password_2fa" and session.get("user_id") != user.user_id:
            await message.answer("❌ Этот код подтверждения создан для другого администратора.")
            return

        await message.answer(
            "Вы пытаетесь авторизоваться в админ-панели.\nПодтверждаете вход?", 
            reply_markup=auth_confirm_kb(token)
        )

    async def auth_approve(self, call: CallbackQuery, callback_data: ConfirmCD, user: User) -> None:
        if not user.is_superuser:
            await call.answer("Нет прав", show_alert=True)
            return
            
        token = callback_data.action.replace("auth_approve_", "")
        session = await _auth_repo.get_session(token)
        if not session:
            await call.message.edit_text("❌ Ошибка: Время ожидания входа истекло (или код уже использован).")
            return

        if session.get("session_type") == "password_2fa":
            if session.get("user_id") != user.user_id:
                await call.answer("Код принадлежит другому администратору", show_alert=True)
                return
            success = await _auth_repo.approve_session(token, user.user_id)
        else:
            success = await _auth_repo.approve_session(token, user.user_id)
        
        if success:
            await call.message.edit_text("✅ Успешный вход! Можете вернуться в браузер.")
        else:
            await call.message.edit_text("❌ Ошибка: Время ожидания входа истекло (или код уже использован).")

    async def auth_reject(self, call: CallbackQuery, callback_data: ConfirmCD, user: User) -> None:
        if not user.is_superuser:
            await call.answer("Нет прав", show_alert=True)
            return

        token = callback_data.action.replace("auth_reject_", "")
        session = await _auth_repo.get_session(token)
        if session and session.get("session_type") == "password_2fa" and session.get("user_id") != user.user_id:
            await call.answer("Код принадлежит другому администратору", show_alert=True)
            return
        await _auth_repo.reject_session(token)
        await call.message.edit_text("❌ Вход отменен.")

    async def cmd_start(self, message: Message, command: CommandObject, user: User, i18n) -> None:
        if not user.has_accepted_agreement:
            settings = get_settings()
            await message.answer(i18n.WELCOME_FIRST, reply_markup=agreement_kb(settings.AGREEMENT_URL))
            return

        await message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb(is_admin=bool(user.is_superuser or user.admin_password_hash)))

    async def accept_agreement(self, call: CallbackQuery, user_service: UserService, user: User, i18n) -> None:
        accepted = await user_service.accept_agreement(call.from_user.id)
        if accepted:
            await call.message.edit_text(i18n.AGREEMENT_ACCEPED)
            await call.message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb(is_admin=bool(user.is_superuser or user.admin_password_hash)))
        else:
            await call.answer("✅", show_alert=False)
            await call.message.edit_text(i18n.WELCOME_MAIN, reply_markup=main_menu_kb(is_admin=bool(user.is_superuser or user.admin_password_hash)))
