from aiogram.filters.callback_data import CallbackData


class MainMenuCD(CallbackData, prefix="main_menu"):
    action: str

class TemplateCD(CallbackData, prefix="template"):
    id: int
    action: str

class PackCD(CallbackData, prefix="pack"):
    id: int
    action: str

class GenerationCD(CallbackData, prefix="gen"):
    id: int
    action: str

class PaymentCD(CallbackData, prefix="pay"):
    pack_id: int
    action: str = "start"

class ConfirmCD(CallbackData, prefix="confirm"):
    action: str
    target_id: int | None = None
