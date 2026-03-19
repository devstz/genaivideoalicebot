from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from db.models import Pack


@dataclass(slots=True)
class PaymentCreateResult:
    provider: str
    invoice_id: str | None
    payment_url: str | None
    status: str
    amount: float | None = None
    currency: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class PaymentWebhookResult:
    event_type: str
    invoice_id: str | None
    status: str | None
    amount: float | None = None
    currency: str | None = None
    buyer_email: str | None = None
    raw: dict[str, Any] | None = None


class BasePaymentProvider(ABC):
    name: str

    @abstractmethod
    async def create_payment(self, *, user_id: int, pack: Pack, buyer_email: str) -> PaymentCreateResult:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
    ) -> PaymentWebhookResult | None:
        raise NotImplementedError
