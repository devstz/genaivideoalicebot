import logging
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import main_menu_kb, settings_kb
from bot.keyboards.callback_data.private import MainMenuCD, ConfirmCD
from bot.states.private import ChangePasswordStates
from config import get_settings
from services.auth.password_service import PasswordService
from services.user_service import UserService


logger = logging.getLogger(__name__)
password_service = PasswordService()


class ProfileRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_profile, MainMenuCD.filter(F.action == "profile"))
        self.callback_query.register(self.show_settings, MainMenuCD.filter(F.action == "settings"))
        self.callback_query.register(self.start_change_password, ConfirmCD.filter(F.action == "settings_change_password"))
        self.callback_query.register(self.toggle_2fa, ConfirmCD.filter(F.action.in_(["settings_toggle_2fa_on", "settings_toggle_2fa_off"])))
        self.message.register(self.handle_current_password, ChangePasswordStates.waiting_current_password)
        self.message.register(self.handle_new_password, ChangePasswordStates.waiting_new_password)
        self.callback_query.register(self.back_to_main, MainMenuCD.filter(F.action == "main"))

    async def show_profile(self, call: CallbackQuery, user_service: UserService, i18n) -> None:
        profile = await user_service.get_profile_info(call.from_user.id)
        user = profile["user"]
        
        ref_link = await create_start_link(call.bot, f"ref_{user.referral_code}", encode=True)
        
        text = i18n.PROFILE_TEXT.format(
            user_id=user.user_id,
            balance=profile["balance"],
            ref_link=ref_link,
            ref_count=profile["referrals_count"]
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=i18n.BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
        
        await call.message.edit_text(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)

    async def back_to_main(self, call: CallbackQuery, i18n) -> None:
        await call.message.edit_text(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())

    async def show_settings(self, call: CallbackQuery, user_service: UserService, i18n) -> None:
        profile = await user_service.get_profile_info(call.from_user.id)
        user = profile["user"]

        telegram_username = f"@{user.username}" if user.username else "не указан"
        admin_login = user.admin_login or "не задан"
        twofa_status = i18n.SETTINGS_TWOFA_ON if user.admin_require_telegram_2fa else i18n.SETTINGS_TWOFA_OFF

        text = i18n.SETTINGS_TEXT.format(
            user_id=user.user_id,
            telegram_username=telegram_username,
            admin_login=admin_login,
            twofa_status=twofa_status,
        )
        await call.message.edit_text(text, reply_markup=settings_kb(user.admin_require_telegram_2fa))

    async def start_change_password(
        self,
        call: CallbackQuery,
        state: FSMContext,
        user_service: UserService,
        i18n,
    ) -> None:
        profile = await user_service.get_profile_info(call.from_user.id)
        user = profile["user"]
        if not user.admin_login or not user.admin_password_hash:
            await call.answer(i18n.SETTINGS_CREDENTIALS_REQUIRED, show_alert=True)
            return

        await state.set_state(ChangePasswordStates.waiting_current_password)
        await call.message.answer(i18n.SETTINGS_ENTER_CURRENT_PASSWORD)

    async def handle_current_password(
        self,
        message: Message,
        state: FSMContext,
        user_service: UserService,
        i18n,
    ) -> None:
        user = await user_service.uow.user_repo.get_by_id(message.from_user.id)
        if not user or not user.admin_password_hash:
            await state.clear()
            await message.answer(i18n.SETTINGS_CREDENTIALS_REQUIRED)
            return

        if not password_service.verify_password(message.text or "", user.admin_password_hash):
            await message.answer(i18n.SETTINGS_PASSWORD_INVALID)
            return

        await state.set_state(ChangePasswordStates.waiting_new_password)
        await message.answer(i18n.SETTINGS_ENTER_NEW_PASSWORD)

    async def handle_new_password(
        self,
        message: Message,
        state: FSMContext,
        user_service: UserService,
        i18n,
    ) -> None:
        settings = get_settings()
        new_password = message.text or ""
        if len(new_password) < settings.ADMIN_PASSWORD_MIN_LENGTH:
            await message.answer(i18n.SETTINGS_PASSWORD_TOO_SHORT)
            return

        user = await user_service.uow.user_repo.get_by_id(message.from_user.id)
        if not user:
            await state.clear()
            return

        user.admin_password_hash = password_service.hash_password(new_password)
        await user_service.uow.user_repo.update(user)
        await state.clear()
        await message.answer(i18n.SETTINGS_PASSWORD_CHANGED)

    async def toggle_2fa(self, call: CallbackQuery, callback_data: ConfirmCD, user_service: UserService, i18n) -> None:
        user = await user_service.uow.user_repo.get_by_id(call.from_user.id)
        if not user:
            await call.answer("❌", show_alert=True)
            return
        if not user.admin_login or not user.admin_password_hash:
            await call.answer(i18n.SETTINGS_CREDENTIALS_REQUIRED, show_alert=True)
            return

        user.admin_require_telegram_2fa = callback_data.action == "settings_toggle_2fa_on"
        await user_service.uow.user_repo.update(user)
        await call.answer(i18n.SETTINGS_2FA_UPDATED, show_alert=False)
        await self.show_settings(call, user_service, i18n)
