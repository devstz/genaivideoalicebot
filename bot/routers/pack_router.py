import logging
import re

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import (
    main_menu_kb,
    packs_kb,
    payment_checkout_kb,
    payment_email_kb,
    payment_lava_kb,
    payment_mock_kb,
)
from bot.keyboards.callback_data.private import ConfirmCD, MainMenuCD, PackCD, PaymentCD
from bot.states.private import PaymentStates
from services.pack_service import PackService


logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PackRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_packs, MainMenuCD.filter(F.action == "packs"))
        self.callback_query.register(self.view_pack, PackCD.filter(F.action == "view"))
        self.callback_query.register(self.process_payment_click, PaymentCD.filter())
        self.callback_query.register(self.skip_payment_email, ConfirmCD.filter(F.action == "pay_skip_email"))
        self.message.register(self.handle_payment_email, PaymentStates.waiting_email)

    async def show_packs(self, call: CallbackQuery, pack_service: PackService, i18n, lang: str) -> None:
        packs = await pack_service.get_active_packs()
        if not packs:
            await call.answer(i18n.PACKS_EMPTY, show_alert=True)
            return

        await call.message.edit_text(i18n.PACKS_LIST, reply_markup=packs_kb(packs, i18n, lang=lang))

    async def view_pack(self, call: CallbackQuery, callback_data: PackCD, pack_service: PackService, i18n, lang: str) -> None:
        from bot.utils.pack_display import pack_price_lines

        pack_id = callback_data.id
        pack = await pack_service.get_pack(pack_id)
        
        if not pack:
            await call.answer("❌", show_alert=True)
            return

        price_line, per_gen_line = pack_price_lines(pack, lang)

        text = i18n.PACK_DETAILS.format(
            name=pack.name,
            description=pack.description or "",
            count=pack.generations_count,
            price_line=price_line,
            per_gen_line=per_gen_line,
        )
        
        provider = await pack_service.get_active_provider_name()
        keyboard = payment_lava_kb(pack.id) if provider == "lava" else payment_mock_kb(pack.id)
        await call.message.edit_text(text, reply_markup=keyboard)

    async def process_payment_click(self, call: CallbackQuery, callback_data: PaymentCD, state: FSMContext, pack_service: PackService, i18n) -> None:
        pack_id = callback_data.pack_id
        if callback_data.action == "mock":
            success = await pack_service.mock_purchase_pack(call.from_user.id, pack_id)
            if success:
                await call.message.edit_text(i18n.PAYMENT_SUCCESS)
                await call.message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())
            else:
                await call.answer(i18n.ERROR_GENERIC, show_alert=True)
            return

        if callback_data.action != "lava":
            await call.answer(i18n.ERROR_GENERIC, show_alert=True)
            return

        user = await pack_service.uow.user_repo.get(call.from_user.id)
        if user and user.email:
            await self._create_lava_payment(
                call=call,
                pack_service=pack_service,
                pack_id=pack_id,
                buyer_email=user.email,
                i18n=i18n,
            )
            return

        await state.set_state(PaymentStates.waiting_email)
        await state.update_data(payment_pack_id=pack_id)
        await call.message.edit_text(i18n.PAYMENT_ENTER_EMAIL, reply_markup=payment_email_kb())

    async def handle_payment_email(self, message: Message, state: FSMContext, pack_service: PackService, i18n) -> None:
        email = (message.text or "").strip().lower()
        if not EMAIL_RE.match(email):
            await message.answer(i18n.PAYMENT_INVALID_EMAIL, reply_markup=payment_email_kb())
            return

        data = await state.get_data()
        pack_id = int(data.get("payment_pack_id", 0))
        if not pack_id:
            await state.clear()
            await message.answer(i18n.ERROR_GENERIC, reply_markup=main_menu_kb())
            return

        user = await pack_service.uow.user_repo.get(message.from_user.id)
        if user:
            user.email = email

        await state.clear()
        await self._create_lava_payment(
            call=message,
            pack_service=pack_service,
            pack_id=pack_id,
            buyer_email=email,
            i18n=i18n,
        )

    async def skip_payment_email(self, call: CallbackQuery, state: FSMContext, pack_service: PackService, i18n) -> None:
        data = await state.get_data()
        pack_id = int(data.get("payment_pack_id", 0))
        if not pack_id:
            await state.clear()
            await call.answer(i18n.ERROR_GENERIC, show_alert=True)
            return

        technical_email = f"user_{call.from_user.id}@autogeneracia21.ru"
        await state.clear()
        await self._create_lava_payment(
            call=call,
            pack_service=pack_service,
            pack_id=pack_id,
            buyer_email=technical_email,
            i18n=i18n,
            warning=i18n.PAYMENT_EMAIL_SKIPPED_WARNING,
        )

    async def _create_lava_payment(
        self,
        *,
        call: CallbackQuery | Message,
        pack_service: PackService,
        pack_id: int,
        buyer_email: str,
        i18n,
        warning: str | None = None,
    ) -> None:
        pack = await pack_service.get_pack(pack_id)
        if not pack or not pack.is_active:
            if hasattr(call, "answer"):
                await call.answer(i18n.ERROR_GENERIC)  # type: ignore[misc]
            return
        if not pack.lava_offer_id:
            if hasattr(call, "answer"):
                await call.answer(i18n.PAYMENT_OFFER_NOT_CONFIGURED)  # type: ignore[misc]
            return

        try:
            result = await pack_service.create_purchase(
                user_id=call.from_user.id,  # type: ignore[union-attr]
                pack_id=pack_id,
                buyer_email=buyer_email,
                force_provider="lava",
            )
        except Exception:
            logger.exception("Failed to create Lava payment")
            if hasattr(call, "answer"):
                await call.answer(i18n.PAYMENT_PROVIDER_UNAVAILABLE)  # type: ignore[misc]
            return

        if not result.success or not result.payment_url:
            if hasattr(call, "answer"):
                await call.answer(result.error or i18n.PAYMENT_PROVIDER_UNAVAILABLE)  # type: ignore[misc]
            return

        text = i18n.PAYMENT_CREATED_OPEN_LINK
        if warning:
            text = f"{warning}\n\n{text}"

        if isinstance(call, CallbackQuery):
            await call.message.edit_text(text, reply_markup=payment_checkout_kb(result.payment_url))
        else:
            await call.answer(text, reply_markup=payment_checkout_kb(result.payment_url))

    async def process_mock_payment(self, call: CallbackQuery, callback_data: PaymentCD, pack_service: PackService, i18n) -> None:
        # Backward compatible handler alias.
        pack_id = callback_data.pack_id
        success = await pack_service.mock_purchase_pack(call.from_user.id, pack_id)

        if success:
            await call.message.edit_text(i18n.PAYMENT_SUCCESS)
            await call.message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())
        else:
            await call.answer(i18n.ERROR_GENERIC, show_alert=True)
