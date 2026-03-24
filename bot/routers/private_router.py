from aiogram.enums import ChatType

from bot.routers.base import BaseRouter
from .start_router import StartRouter
from .template_router import TemplateRouter
from .postcard_router import PostcardRouter
from .pack_router import PackRouter
from .profile_router import ProfileRouter


class PrivateRouter(BaseRouter):
    chat_types = [ChatType.PRIVATE]

    def __init__(self) -> None:
        super().__init__()

    def _include_routers(self) -> None:
        self.include_routers(
            StartRouter(),
            TemplateRouter(),
            PostcardRouter(),
            PackRouter(),
            ProfileRouter()
        )
