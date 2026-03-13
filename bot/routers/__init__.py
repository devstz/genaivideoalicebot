from aiogram import Dispatcher
from .private_router import PrivateRouter


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(PrivateRouter())
