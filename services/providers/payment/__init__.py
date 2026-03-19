from __future__ import annotations

from .base import BasePaymentProvider, PaymentCreateResult, PaymentWebhookResult
from .lava_provider import LavaPaymentProvider
from .mock_provider import MockPaymentProvider


def get_payment_provider(provider_name: str) -> BasePaymentProvider:
    normalized = (provider_name or "mock").strip().lower()
    if normalized == "lava":
        return LavaPaymentProvider()
    return MockPaymentProvider()


__all__ = [
    "BasePaymentProvider",
    "PaymentCreateResult",
    "PaymentWebhookResult",
    "LavaPaymentProvider",
    "MockPaymentProvider",
    "get_payment_provider",
]
