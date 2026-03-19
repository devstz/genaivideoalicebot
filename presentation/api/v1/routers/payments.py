from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from bot.builder.instance_bot import create_bot
from config.settings import get_settings
from presentation.dependencies import get_uow_dependency
from db.uow import SQLAlchemyUnitOfWork
from services.pack_service import PackService
from services.providers.payment import get_payment_provider


payments_router = APIRouter(prefix="/payments", tags=["Payments"])


@payments_router.post("/webhook/lava")
async def lava_webhook(
    request: Request,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
):
    try:
        body = await request.json()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}")

    provider = get_payment_provider("lava")
    webhook = provider.parse_webhook(headers=dict(request.headers), body=body)
    if not webhook:
        raise HTTPException(status_code=401, detail="Invalid webhook auth or payload")

    if not webhook.invoice_id:
        return {"status": "ignored", "reason": "missing_contract_id"}

    service = PackService(uow)
    if webhook.event_type == "payment.success":
        confirmed = await service.confirm_purchase(
            external_invoice_id=webhook.invoice_id,
            amount=webhook.amount,
            currency=webhook.currency,
            buyer_email=webhook.buyer_email,
        )
        if confirmed:
            purchase = await uow.purchase_repo.get_by_external_invoice_id(webhook.invoice_id)
            if purchase:
                pack = await uow.pack_repo.get(purchase.pack_id)
                if pack:
                    settings = get_settings()
                    bot = create_bot(settings.TOKEN)
                    try:
                        await bot.send_message(
                            purchase.user_id,
                            f"✅ Оплата подтверждена! Вам начислено <b>{pack.generations_count}</b> генераций.",
                        )
                    finally:
                        await bot.session.close()
    elif webhook.event_type == "payment.failed":
        await service.fail_purchase(
            external_invoice_id=webhook.invoice_id,
            amount=webhook.amount,
            currency=webhook.currency,
            buyer_email=webhook.buyer_email,
        )

    return {"status": "ok"}
