from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from db.models import Pack

from .base import BasePaymentProvider, PaymentCreateResult, PaymentWebhookResult


class MockPaymentProvider(BasePaymentProvider):
    name = "mock"

    async def create_payment(self, *, user_id: int, pack: Pack, buyer_email: str) -> PaymentCreateResult:
        return PaymentCreateResult(
            provider=self.name,
            invoice_id=f"mock-{uuid4()}",
            payment_url=None,
            status="completed",
            amount=float(pack.price),
            currency="RUB",
            raw={"mock": True, "user_id": user_id, "pack_id": pack.id, "buyer_email": buyer_email},
        )

    def parse_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
    ) -> PaymentWebhookResult | None:
        return None
