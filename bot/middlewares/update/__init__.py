from aiogram import Dispatcher

from .uow_middleware import UoWMiddleware
from .user_middleware import UserMiddleware
from .service_middleware import ServiceMiddleware
from .i18n_middleware import I18nMiddleware
from .user_action_middleware import UserActionMiddleware


def connect_update_middlewares(dp: Dispatcher) -> None:
    # Order: UoW → User → i18n → Services → ActionLog
    dp.update.middleware(UoWMiddleware())
    dp.update.middleware(UserMiddleware())
    dp.update.middleware(I18nMiddleware())
    dp.update.middleware(ServiceMiddleware())
    dp.update.middleware(UserActionMiddleware())
