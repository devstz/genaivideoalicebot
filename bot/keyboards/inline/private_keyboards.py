from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.locales.ru import (
    BTN_AGREEMENT, BTN_ACCEPT_AGREEMENT,
    BTN_REVIVE_PHOTO, BTN_PACKS, BTN_PROFILE,
    BTN_BACK, BTN_BUY_PACK, BTN_MOCK_PAY,
    BTN_SKIP, BTN_CONFIRM, BTN_CUSTOM_PROMPT
)
from bot.keyboards.callback_data.private import (
    MainMenuCD, TemplateCD, PackCD, PaymentCD, ConfirmCD
)
from db.models import Template, Pack


def agreement_kb(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_AGREEMENT, url=url)
    builder.button(text=BTN_ACCEPT_AGREEMENT, callback_data=MainMenuCD(action="accept_agreement"))
    builder.adjust(1)
    return builder.as_markup()

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_REVIVE_PHOTO, callback_data=MainMenuCD(action="templates"))
    builder.button(text=BTN_PACKS, callback_data=MainMenuCD(action="packs"))
    builder.button(text=BTN_PROFILE, callback_data=MainMenuCD(action="profile"))
    builder.adjust(1, 2)
    return builder.as_markup()

def templates_kb(templates: list[Template]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_CUSTOM_PROMPT, callback_data=MainMenuCD(action="custom_prompt"))
    for t in templates:
        builder.button(text=t.name, callback_data=TemplateCD(id=t.id, action="view"))
    builder.adjust(1, 2)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
    return builder.as_markup()

def template_preview_kb(template_id: int, has_balance: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_balance:
        builder.button(text=BTN_CONFIRM, callback_data=TemplateCD(id=template_id, action="start_gen"))
    else:
        builder.button(text=BTN_PACKS, callback_data=MainMenuCD(action="packs"))
    
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="templates"))
    builder.adjust(1)
    return builder.as_markup()

def ask_photo_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_BACK, callback_data=ConfirmCD(action="gen_back_to_templates"))
    return builder.as_markup()

def skip_wishes_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_SKIP, callback_data=ConfirmCD(action="skip_wishes"))
    builder.button(text=BTN_BACK, callback_data=ConfirmCD(action="gen_back_to_photo"))
    builder.adjust(2)
    return builder.as_markup()

def packs_kb(packs: list[Pack]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in packs:
        builder.button(text=BTN_BUY_PACK.format(name=p.name, price=str(int(p.price)), count=p.generations_count), callback_data=PackCD(id=p.id, action="view"))
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
    return builder.as_markup()

def payment_mock_kb(pack_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_MOCK_PAY, callback_data=PaymentCD(pack_id=pack_id))
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="packs"))
    builder.adjust(1)
    return builder.as_markup()
def auth_confirm_kb(token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Разрешить", callback_data=ConfirmCD(action=f"auth_approve_{token}"))
    builder.button(text="❌ Отменить", callback_data=ConfirmCD(action=f"auth_reject_{token}"))
    builder.adjust(2)
    return builder.as_markup()
