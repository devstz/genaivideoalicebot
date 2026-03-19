from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from config.settings import get_settings
from db.models import User
from db.uow import SQLAlchemyUnitOfWork
from presentation.dependencies import get_uow_dependency
from presentation.dependencies.security import get_current_admin


settings_router = APIRouter(prefix="/settings", tags=["Admin Settings"])


class PaymentProviderRead(BaseModel):
    provider: Literal["mock", "lava"]
    lava_api_key_configured: bool
    lava_webhook_secret_configured: bool


class PaymentProviderUpdate(BaseModel):
    provider: Literal["mock", "lava"]


@settings_router.get("/payment", response_model=PaymentProviderRead)
async def get_payment_settings(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    settings = get_settings()
    db_provider = await uow.global_setting_repo.get("payment_provider")
    provider = (db_provider or settings.PAYMENT_PROVIDER or "mock").strip().lower()
    if provider not in {"mock", "lava"}:
        provider = "mock"

    return PaymentProviderRead(
        provider=provider,  # type: ignore[arg-type]
        lava_api_key_configured=bool(settings.LAVA_API_KEY),
        lava_webhook_secret_configured=bool(settings.LAVA_WEBHOOK_SECRET),
    )


@settings_router.put("/payment", response_model=PaymentProviderRead)
async def update_payment_settings(
    payload: PaymentProviderUpdate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    await uow.global_setting_repo.set("payment_provider", payload.provider)
    return await get_payment_settings(uow=uow, admin=admin)


