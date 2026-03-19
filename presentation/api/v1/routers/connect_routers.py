from fastapi import FastAPI

from .public.health import init_router as init_public_health_router
from .admin.auth import router as admin_auth_router
from .admin.dashboard import dashboard_router
from .admin.templates import templates_router
from .admin.generations import generations_router
from .admin.lava import lava_router
from .admin.mailings import mailings_router
from .admin.packs import packs_router
from .admin.settings import settings_router
from .admin.utm import utm_router
from .payments import payments_router

def connect_routers(app: FastAPI) -> None:
    init_public_health_router(app)
    app.include_router(admin_auth_router, prefix="/api/v1")
    app.include_router(dashboard_router, prefix="/api/v1/admin")
    app.include_router(templates_router, prefix="/api/v1/admin")
    app.include_router(generations_router, prefix="/api/v1/admin")
    app.include_router(lava_router, prefix="/api/v1/admin")
    app.include_router(mailings_router, prefix="/api/v1/admin")
    app.include_router(packs_router, prefix="/api/v1/admin")
    app.include_router(settings_router, prefix="/api/v1/admin")
    app.include_router(utm_router, prefix="/api/v1/admin")
    app.include_router(payments_router, prefix="/api/v1")