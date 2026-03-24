from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.locales.ru import (
    BTN_AGREEMENT, BTN_ACCEPT_AGREEMENT,
    BTN_REVIVE_PHOTO, BTN_PACKS, BTN_PROFILE,
    BTN_BACK, BTN_BUY_PACK, BTN_MOCK_PAY, BTN_LAVA_PAY, BTN_PAY_OPEN_LINK, BTN_PAY_SKIP_EMAIL,
    BTN_SKIP, BTN_CONFIRM, BTN_CUSTOM_PROMPT,
    BTN_SETTINGS, BTN_CHANGE_PASSWORD, BTN_TOGGLE_2FA_ON, BTN_TOGGLE_2FA_OFF, BTN_SETTINGS_REFRESH,
    BTN_POSTCARDS, BTN_HELP, BTN_CUSTOM_PROMPT_MAIN,
)
from bot.keyboards.callback_data.private import (
    MainMenuCD, TemplateCD, PackCD, PaymentCD, ConfirmCD, PostcardCD
)
from db.models import Template, Pack


def agreement_kb(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_AGREEMENT, url=url)
    builder.button(text=BTN_ACCEPT_AGREEMENT, callback_data=MainMenuCD(action="accept_agreement"))
    builder.adjust(1)
    return builder.as_markup()

def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_REVIVE_PHOTO, callback_data=MainMenuCD(action="templates"))
    builder.button(text=BTN_POSTCARDS, callback_data=MainMenuCD(action="postcards"))
    builder.button(text=BTN_CUSTOM_PROMPT_MAIN, callback_data=MainMenuCD(action="custom_prompt"))
    builder.button(text=BTN_PACKS, callback_data=MainMenuCD(action="packs"))
    builder.button(text=BTN_PROFILE, callback_data=MainMenuCD(action="profile"))
    builder.button(text=BTN_HELP, callback_data=MainMenuCD(action="help"))
    if is_admin:
        builder.button(text=BTN_SETTINGS, callback_data=MainMenuCD(action="settings"))
        builder.adjust(2, 1, 2, 2)
    else:
        builder.adjust(2, 1, 2, 1)
    return builder.as_markup()

def templates_kb(templates: list[Template]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in templates:
        builder.button(text=t.name, callback_data=TemplateCD(id=t.id, action="view"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
    return builder.as_markup()

def postcards_kb(postcards: list[Template]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in postcards:
        builder.button(text=p.name, callback_data=PostcardCD(id=p.id, action="view"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
    return builder.as_markup()

def postcard_preview_kb(postcard_id: int, has_balance: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_balance:
        builder.button(text=BTN_CONFIRM, callback_data=PostcardCD(id=postcard_id, action="start_gen"))
    else:
        builder.button(text=BTN_PACKS, callback_data=MainMenuCD(action="packs"))
    
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="postcards"))
    builder.adjust(1)
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

def packs_kb(packs: list[Pack], i18n, *, lang: str = "ru") -> InlineKeyboardMarkup:
    from bot.utils.pack_display import format_price_line, pick_amount_and_currency

    builder = InlineKeyboardBuilder()
    for p in packs:
        amt, cur = pick_amount_and_currency(p, lang)
        price_line = format_price_line(amt, cur)
        builder.button(
            text=i18n.BTN_BUY_PACK.format(name=p.name, price_line=price_line, count=p.generations_count),
            callback_data=PackCD(id=p.id, action="view"),
        )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=BTN_BACK, callback_data=MainMenuCD(action="main").pack()))
    return builder.as_markup()

def payment_mock_kb(pack_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_MOCK_PAY, callback_data=PaymentCD(pack_id=pack_id, action="mock"))
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="packs"))
    builder.adjust(1)
    return builder.as_markup()


def payment_lava_kb(pack_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_LAVA_PAY, callback_data=PaymentCD(pack_id=pack_id, action="lava"))
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="packs"))
    builder.adjust(1)
    return builder.as_markup()


def payment_email_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_PAY_SKIP_EMAIL, callback_data=ConfirmCD(action="pay_skip_email"))
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="packs"))
    builder.adjust(1)
    return builder.as_markup()


def payment_checkout_kb(payment_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_PAY_OPEN_LINK, url=payment_url)
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="packs"))
    builder.adjust(1)
    return builder.as_markup()
def auth_confirm_kb(token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Разрешить", callback_data=ConfirmCD(action=f"auth_approve_{token}"))
    builder.button(text="❌ Отменить", callback_data=ConfirmCD(action=f"auth_reject_{token}"))
    builder.adjust(2)
    return builder.as_markup()


def settings_kb(twofa_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_CHANGE_PASSWORD, callback_data=ConfirmCD(action="settings_change_password"))
    builder.button(
        text=BTN_TOGGLE_2FA_OFF if twofa_enabled else BTN_TOGGLE_2FA_ON,
        callback_data=ConfirmCD(action=f"settings_toggle_2fa_{'off' if twofa_enabled else 'on'}"),
    )
    builder.button(text=BTN_SETTINGS_REFRESH, callback_data=MainMenuCD(action="settings"))
    builder.button(text=BTN_BACK, callback_data=MainMenuCD(action="main"))
    builder.adjust(1, 1, 2)
    return builder.as_markup()
