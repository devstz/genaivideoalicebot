from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

import httpx
from lava_top_sdk import Currency, FeedVisibility, LavaClient, LavaClientConfig

from config.settings import get_settings
from db.models import Pack

from .base import BasePaymentProvider, PaymentCreateResult, PaymentWebhookResult

logger = logging.getLogger(__name__)


class LavaPaymentProvider(BasePaymentProvider):
    """
    Lava.top: актуальный API — POST /api/v3/invoice; запасные варианты v2 и SDK.
    Список продуктов: feedVisibility=ALL (иначе скрытые из ленты не попадают в админку).
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

    async def create_payment(self, *, user_id: int, pack: Pack, buyer_email: str, payment_method: str | None = None) -> PaymentCreateResult:
        if not self.settings.LAVA_API_KEY:
            raise ValueError("LAVA_API_KEY is not configured")
        if not pack.lava_offer_id:
            raise ValueError("Pack is not connected to Lava offerId")

        last_error: Exception | None = None
        for name, coro_factory in (
            ("v3", lambda: self._create_payment_http_v3(buyer_email=buyer_email, pack=pack, payment_method=payment_method)),
            ("v2", lambda: self._create_payment_http_v2(buyer_email=buyer_email, pack=pack, payment_method=payment_method)),
            ("sdk", lambda: self._create_payment_sdk(buyer_email=buyer_email, pack=pack, payment_method=payment_method)),
        ):
            try:
                return await coro_factory()
            except Exception as exc:
                last_error = exc
                logger.warning("Lava invoice via %s failed: %s", name, exc)

        assert last_error is not None
        raise last_error

    def _payment_result_from_invoice_json(self, data: dict[str, Any]) -> PaymentCreateResult:
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

    async def _create_payment_http_v3(self, *, buyer_email: str, pack: Pack, payment_method: str | None = None) -> PaymentCreateResult:
        """Текущий контракт Lava (см. gate.lava.top/docs): минимальное тело без periodicity."""
        payload = {
            "email": buyer_email,
            "offerId": pack.lava_offer_id,
            "currency": "RUB",
        }
        if payment_method == "sbp":
            payload["paymentProvider"] = "PAY2ME"
            payload["paymentMethod"] = "SBP"
        headers = {
            "X-Api-Key": self.settings.LAVA_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.api_base}/api/v3/invoice", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return self._payment_result_from_invoice_json(data)

    async def _create_payment_http_v2(self, *, buyer_email: str, pack: Pack, payment_method: str | None = None) -> PaymentCreateResult:
        payload = {
            "email": buyer_email,
            "offerId": pack.lava_offer_id,
            "currency": "RUB",
            "periodicity": "ONE_TIME",
        }
        if payment_method == "sbp":
            payload["paymentProvider"] = "PAY2ME"
            payload["paymentMethod"] = "SBP"
        headers = {
            "X-Api-Key": self.settings.LAVA_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.api_base}/api/v2/invoice", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return self._payment_result_from_invoice_json(data)

    async def _create_payment_sdk(self, *, buyer_email: str, pack: Pack, payment_method: str | None = None) -> PaymentCreateResult:
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
                products = self._lava_client().get_products(
                    feed_visibility=FeedVisibility.ALL,
                    show_all_subscription_periods=True,
                )
                return {"items": [p.model_dump(mode="json") for p in products]}

            return await asyncio.to_thread(_list_sdk)
        except Exception as exc:
            logger.warning("Lava SDK get_products failed, raw HTTP fallback: %s", exc)
            headers = {
                "X-Api-Key": self.settings.LAVA_API_KEY,
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{self.api_base}/api/v2/products",
                    headers=headers,
                    params={
                        "feedVisibility": "ALL",
                        "showAllSubscriptionPeriods": "true",
                    },
                )
                response.raise_for_status()
                return response.json()

    async def get_offer_prices_by_currency(self, offer_id: str) -> dict[str, float]:
        """Все суммы ONE_TIME по валютам для offerId (RUB, USD, EUR, …)."""
        data = await self.list_products()
        out: dict[str, float] = {}
        for item in (data.get("items") or []):
            product = item.get("data", item) if isinstance(item, dict) else item
            if not isinstance(product, dict):
                continue
            for offer in (product.get("offers") or []):
                if not isinstance(offer, dict) or str(offer.get("id", "")) != offer_id:
                    continue
                for p in offer.get("prices") or []:
                    if not isinstance(p, dict):
                        continue
                    per = str(p.get("periodicity") or "ONE_TIME").upper()
                    if per != "ONE_TIME":
                        continue
                    cur = str(p.get("currency") or "").upper()
                    amt = p.get("amount")
                    if cur and isinstance(amt, (int, float)):
                        out[cur] = float(amt)
                return out
        return out

    async def get_offer_price(self, offer_id: str) -> float | None:
        """Сумма в RUB для обратной совместимости (mock price column)."""
        prices = await self.get_offer_prices_by_currency(offer_id)
        return prices.get("RUB") or (next(iter(prices.values())) if prices else None)
