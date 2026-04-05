import logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import (
    postcards_kb, postcard_preview_kb, skip_wishes_kb, ask_photo_kb, main_menu_kb
)
from bot.keyboards.callback_data.private import MainMenuCD, PostcardCD, ConfirmCD
from bot.states.private import GenerationStates
from bot.routers.helper import edit_message
from services.template_service import TemplateService
from services.user_service import UserService
from services.generation_service import GenerationService


logger = logging.getLogger(__name__)


class PostcardRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_postcards, MainMenuCD.filter(F.action == "postcards"))
        self.callback_query.register(self.show_help, MainMenuCD.filter(F.action == "help"))
        self.callback_query.register(self.view_postcard, PostcardCD.filter(F.action == "view"))
        self.callback_query.register(self.start_generation, PostcardCD.filter(F.action == "start_gen"))

    async def show_postcards(self, call: CallbackQuery, template_service: TemplateService, i18n) -> None:
        postcards = await template_service.get_active_postcards()
        if not postcards:
            await call.answer(i18n.POSTCARD_EMPTY, show_alert=True)
            return

        await edit_message(call, text=i18n.POSTCARD_LIST, reply_markup=postcards_kb(postcards))

    async def show_help(self, call: CallbackQuery, i18n) -> None:
        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=i18n.BTN_BACK, callback_data=MainMenuCD(action="main").pack()))

        await edit_message(call, text=i18n.HELP_TEXT, reply_markup=builder.as_markup())

    async def view_postcard(self, call: CallbackQuery, callback_data: PostcardCD, template_service: TemplateService, user_service: UserService, i18n) -> None:
        postcard_id = callback_data.id
        postcard = await template_service.get_template(postcard_id)

        if not postcard:
            await call.answer("❌", show_alert=True)
            return

        profile = await user_service.get_profile_info(call.from_user.id)
        has_balance = profile["balance"] > 0

        text = i18n.template_preview(postcard.name, has_balance)
        kb = postcard_preview_kb(postcard.id, has_balance)

        preview_video = postcard.preview_video_path
        preview_image = postcard.preview_image_path
        
        if preview_video:
            await edit_message(call, text=text, reply_markup=kb, video=preview_video)
        elif preview_image:
            await edit_message(call, text=text, reply_markup=kb, photo=preview_image)
        else:
            await edit_message(call, text=text, reply_markup=kb)

    async def start_generation(
        self,
        call: CallbackQuery,
        callback_data: PostcardCD,
        state: FSMContext,
        generation_service: GenerationService,
        i18n,
    ) -> None:
        if not await generation_service.can_create_generation(call.from_user.id):
            await call.answer(i18n.GENERATION_ALREADY_IN_PROGRESS_ALERT, show_alert=True)
            return

        template_id = callback_data.id
        await state.update_data(template_id=template_id, is_custom_prompt=False)
        await state.set_state(GenerationStates.uploading_photo)
        await edit_message(call, text=i18n.ASK_PHOTO, reply_markup=ask_photo_kb())
