import logging
from aiogram import F
from aiogram.types import CallbackQuery

from bot.routers.base import BaseRouter
from bot.keyboards.inline.private_keyboards import packs_kb, payment_mock_kb, main_menu_kb
from bot.keyboards.callback_data.private import MainMenuCD, PackCD, PaymentCD
from services.pack_service import PackService


logger = logging.getLogger(__name__)


class PackRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_packs, MainMenuCD.filter(F.action == "packs"))
        self.callback_query.register(self.view_pack, PackCD.filter(F.action == "view"))
        self.callback_query.register(self.process_mock_payment, PaymentCD.filter())

    async def show_packs(self, call: CallbackQuery, pack_service: PackService, i18n) -> None:
        packs = await pack_service.get_active_packs()
        if not packs:
            await call.answer(i18n.PACKS_EMPTY, show_alert=True)
            return

        await call.message.edit_text(i18n.PACKS_LIST, reply_markup=packs_kb(packs))

    async def view_pack(self, call: CallbackQuery, callback_data: PackCD, pack_service: PackService, i18n) -> None:
        pack_id = callback_data.id
        pack = await pack_service.get_pack(pack_id)
        
        if not pack:
            await call.answer("❌", show_alert=True)
            return

        price = int(pack.price)
        per_gen = round(price / pack.generations_count)

        text = i18n.PACK_DETAILS.format(
            name=pack.name,
            description=pack.description or "",
            count=pack.generations_count,
            price=price,
            per_gen=per_gen,
        )
        
        await call.message.edit_text(text, reply_markup=payment_mock_kb(pack.id))

    async def process_mock_payment(self, call: CallbackQuery, callback_data: PaymentCD, pack_service: PackService, i18n) -> None:
        pack_id = callback_data.pack_id
        success = await pack_service.mock_purchase_pack(call.from_user.id, pack_id)
        
        if success:
            await call.message.edit_text(i18n.PAYMENT_SUCCESS)
            await call.message.answer(i18n.WELCOME_MAIN, reply_markup=main_menu_kb())
        else:
            await call.answer(i18n.ERROR_GENERIC, show_alert=True)
