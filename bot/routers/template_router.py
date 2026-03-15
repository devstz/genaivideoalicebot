import logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import (
    templates_kb, template_preview_kb, skip_wishes_kb, ask_photo_kb, main_menu_kb
)
from bot.keyboards.callback_data.private import MainMenuCD, TemplateCD, ConfirmCD
from bot.states.private import GenerationStates
from services.template_service import TemplateService
from services.user_service import UserService
from services.generation_service import GenerationService


logger = logging.getLogger(__name__)


class TemplateRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_templates, MainMenuCD.filter(F.action == "templates"))
        self.callback_query.register(self.start_custom_prompt, MainMenuCD.filter(F.action == "custom_prompt"))
        self.callback_query.register(self.view_template, TemplateCD.filter(F.action == "view"))
        self.callback_query.register(self.start_generation, TemplateCD.filter(F.action == "start_gen"))
        self.message.register(self.process_photo, GenerationStates.uploading_photo)
        self.message.register(self.process_wishes, GenerationStates.entering_wishes)
        self.callback_query.register(self.skip_wishes, ConfirmCD.filter(F.action == "skip_wishes"), GenerationStates.entering_wishes)
        self.callback_query.register(self.back_from_photo, ConfirmCD.filter(F.action == "gen_back_to_templates"), GenerationStates.uploading_photo)
        self.callback_query.register(self.back_from_wishes, ConfirmCD.filter(F.action == "gen_back_to_photo"), GenerationStates.entering_wishes)

    async def show_templates(self, call: CallbackQuery, template_service: TemplateService, i18n) -> None:
        templates = await template_service.get_active_templates()
        if not templates:
            await call.answer(i18n.TEMPLATE_EMPTY, show_alert=True)
            return
            
        await call.message.edit_text(i18n.TEMPLATE_LIST, reply_markup=templates_kb(templates))

    async def view_template(self, call: CallbackQuery, callback_data: TemplateCD, template_service: TemplateService, user_service: UserService, i18n) -> None:
        template_id = callback_data.id
        template = await template_service.get_template(template_id)
        
        if not template:
            await call.answer("❌", show_alert=True)
            return

        profile = await user_service.get_profile_info(call.from_user.id)
        has_balance = profile["balance"] > 0
        
        text = i18n.template_preview(template.name, has_balance)
        kb = template_preview_kb(template.id, has_balance)
        
        await call.message.edit_text(text, reply_markup=kb)

    async def start_generation(self, call: CallbackQuery, callback_data: TemplateCD, state: FSMContext, i18n) -> None:
        template_id = callback_data.id
        await state.update_data(template_id=template_id, is_custom_prompt=False)
        await state.set_state(GenerationStates.uploading_photo)
        await call.message.edit_text(i18n.ASK_PHOTO, reply_markup=ask_photo_kb())

    async def start_custom_prompt(self, call: CallbackQuery, state: FSMContext, user_service: UserService, i18n) -> None:
        profile = await user_service.get_profile_info(call.from_user.id)
        if profile["balance"] <= 0:
            await call.answer(i18n.INSUFFICIENT_BALANCE_ALERT, show_alert=True)
            return
        await state.update_data(template_id=None, is_custom_prompt=True)
        await state.set_state(GenerationStates.uploading_photo)
        await call.message.edit_text(i18n.ASK_PHOTO, reply_markup=ask_photo_kb())

    async def back_from_photo(self, call: CallbackQuery, state: FSMContext, template_service: TemplateService, i18n) -> None:
        await state.clear()
        templates = await template_service.get_active_templates()
        if not templates:
            await call.answer(i18n.TEMPLATE_EMPTY, show_alert=True)
            return
        await call.message.edit_text(i18n.TEMPLATE_LIST, reply_markup=templates_kb(templates))

    async def back_from_wishes(self, call: CallbackQuery, state: FSMContext, i18n) -> None:
        await state.set_state(GenerationStates.uploading_photo)
        await call.message.edit_text(i18n.ASK_PHOTO, reply_markup=ask_photo_kb())

    async def process_photo(self, message: Message, state: FSMContext, i18n) -> None:
        if not message.photo:
            await message.answer(i18n.ERROR_NOT_PHOTO)
            return

        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)

        data = await state.get_data()
        is_custom = data.get("is_custom_prompt", False)
        await state.set_state(GenerationStates.entering_wishes)

        prompt_msg = i18n.ASK_CUSTOM_PROMPT if is_custom else i18n.ASK_WISHES
        sent = await message.answer(prompt_msg, reply_markup=skip_wishes_kb())
        await state.update_data(prompt_message_id=sent.message_id)

    async def _finalize_prompt_message(self, message: Message, prompt_message_id: int | None, i18n) -> None:
        if not prompt_message_id:
            return
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=prompt_message_id,
                text=i18n.PROMPT_ACCEPTED,
                reply_markup=None,
            )
        except Exception as e:
            logger.debug(f"Failed to finalize prompt message {prompt_message_id}: {e}")

    async def _finish_generation_request(self, user_id: int, message: Message, state: FSMContext, generation_service: GenerationService, i18n, wishes: str | None = None) -> None:
        data = await state.get_data()
        template_id = data.get("template_id")
        photo_id = data.get("photo_id")
        prompt_message_id = data.get("prompt_message_id")

        await self._finalize_prompt_message(message, prompt_message_id, i18n)

        generation = await generation_service.create_generation_request(
            user_id=user_id,
            input_photo_path=photo_id,
            user_prompt=wishes,
            template_id=template_id,
        )

        await state.clear()

        if not generation:
            await message.answer(i18n.INSUFFICIENT_BALANCE)
            await message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())
            return

        try:
            await message.bot.send_message_draft(
                chat_id=user_id,
                draft_id=generation.id,
                text=i18n.GENERATION_QUEUED,
            )
        except Exception:
            await message.answer(i18n.GENERATION_STARTED)
        await message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())


    async def process_wishes(self, message: Message, state: FSMContext, generation_service: GenerationService, i18n) -> None:
        wishes = message.text
        await self._finish_generation_request(message.from_user.id, message, state, generation_service, i18n, wishes)

    async def skip_wishes(self, call: CallbackQuery, state: FSMContext, generation_service: GenerationService, i18n) -> None:
        await self._finish_generation_request(call.from_user.id, call.message, state, generation_service, i18n, wishes=None)
