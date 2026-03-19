from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

import httpx
from lava_top_sdk import Currency, LavaClient, LavaClientConfig

from config.settings import get_settings
from db.models import Pack

from .base import BasePaymentProvider, PaymentCreateResult, PaymentWebhookResult

logger = logging.getLogger(__name__)


class LavaPaymentProvider(BasePaymentProvider):
    """
    Lava.top: официальный lava-top-sdk (синхронный requests) + asyncio.to_thread.
    Fallback на прямой HTTP (v2 invoice / сырой список продуктов), если SDK не совпал с ответом API.
    """

    name = "lava"
    api_base = "https://gate.lava.top"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: LavaClient | None = None

    def _lava_client(self) -> LavaClient:
        if self._client is None:
            self._client = LavaClient(
                LavaClientConfig(
                    api_key=self.settings.LAVA_API_KEY,
                    env="production",
                    base_url=self.api_base,
                    timeout=20,
                    max_retries=2,
                )
            )
        return self._client

    async def create_payment(self, *, user_id: int, pack: Pack, buyer_email: str) -> PaymentCreateResult:
        if not self.settings.LAVA_API_KEY:
            raise ValueError("LAVA_API_KEY is not configured")
        if not pack.lava_offer_id:
            raise ValueError("Pack is not connected to Lava offerId")

        try:

            def _create() -> PaymentCreateResult:
                inv = self._lava_client().create_one_time_payment(
                    email=buyer_email,
                    offer_id=pack.lava_offer_id,
                    currency=Currency.RUB,
                )
                raw = inv.model_dump(mode="json")
                return PaymentCreateResult(
                    provider=self.name,
                    invoice_id=inv.id,
                    payment_url=inv.paymentUrl,
                    status=(inv.status.value if hasattr(inv.status, "value") else str(inv.status)).lower(),
                    amount=float(inv.amountTotal.amount),
                    currency=inv.amountTotal.currency.value
                    if hasattr(inv.amountTotal.currency, "value")
                    else str(inv.amountTotal.currency),
                    raw=raw,
                )

            return await asyncio.to_thread(_create)
        except Exception as exc:
            logger.warning("Lava SDK invoice failed, HTTP v2 fallback: %s", exc)
            return await self._create_payment_http_v2(buyer_email=buyer_email, pack=pack)

    async def _create_payment_http_v2(self, *, buyer_email: str, pack: Pack) -> PaymentCreateResult:
        # gate.lava.top отдаёт 404 на /api/v3/invoice; рабочий путь — /api/v2/invoice (как в lava-top-sdk).
        payload = {
            "email": buyer_email,
            "offerId": pack.lava_offer_id,
            "currency": "RUB",
            "periodicity": "ONE_TIME",
        }
        headers = {
            "X-Api-Key": self.settings.LAVA_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.api_base}/api/v2/invoice", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        amount_total = data.get("amountTotal") or {}
        return PaymentCreateResult(
            provider=self.name,
            invoice_id=data.get("id"),
            payment_url=data.get("paymentUrl"),
            status=str(data.get("status") or "").lower(),
            amount=float(amount_total.get("amount")) if amount_total.get("amount") is not None else None,
            currency=amount_total.get("currency"),
            raw=data,
        )

    def parse_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
    ) -> PaymentWebhookResult | None:
        # SDK ожидает HMAC в заголовке `signature`; у Lava в кабинете часто задают секрет как API key в X-Api-Key.
        # Оставляем прежнюю схему, совместимую с текущим FastAPI webhook.
        expected_secret = (self.settings.LAVA_WEBHOOK_SECRET or "").strip()
        if not expected_secret:
            return None

        header_secret = headers.get("x-api-key") or headers.get("X-Api-Key")
        if not header_secret or header_secret.strip() != expected_secret:
            return None

        event_type = str(body.get("eventType") or "")
        if not event_type:
            return None

        buyer = body.get("buyer") or {}
        return PaymentWebhookResult(
            event_type=event_type,
            invoice_id=body.get("contractId"),
            status=str(body.get("status") or "").lower() or None,
            amount=float(body.get("amount")) if body.get("amount") is not None else None,
            currency=body.get("currency"),
            buyer_email=buyer.get("email") if isinstance(buyer, dict) else None,
            raw=dict(body),
        )

    async def list_products(self) -> dict[str, Any]:
        if not self.settings.LAVA_API_KEY:
            raise ValueError("LAVA_API_KEY is not configured")

        try:

            def _list_sdk() -> dict[str, Any]:
                products = self._lava_client().get_products()
                return {"items": [p.model_dump(mode="json") for p in products]}

            return await asyncio.to_thread(_list_sdk)
        except Exception as exc:
            logger.warning("Lava SDK get_products failed, raw HTTP fallback: %s", exc)
            headers = {
                "X-Api-Key": self.settings.LAVA_API_KEY,
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{self.api_base}/api/v2/products", headers=headers)
                response.raise_for_status()
                return response.json()

    async def get_offer_price(self, offer_id: str) -> float | None:
        """Fetch the first price amount for a given offerId from the Lava catalog."""
        data = await self.list_products()
        for item in (data.get("items") or []):
            product = item.get("data", item) if isinstance(item, dict) else item
            if not isinstance(product, dict):
                continue
            for offer in (product.get("offers") or []):
                if not isinstance(offer, dict) or str(offer.get("id", "")) != offer_id:
                    continue
                prices = offer.get("prices") or []
                if prices and isinstance(prices[0], dict):
                    amount = prices[0].get("amount")
                    if isinstance(amount, (int, float)):
                        return float(amount)
        return None
