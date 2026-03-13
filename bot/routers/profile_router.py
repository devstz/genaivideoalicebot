import logging
from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import main_menu_kb
from bot.keyboards.callback_data.private import MainMenuCD
from services.user_service import UserService


logger = logging.getLogger(__name__)


class ProfileRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_profile, MainMenuCD.filter(F.action == "profile"))
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
