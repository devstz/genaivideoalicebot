"""Агрегация выручки по фактическим суммам оплат (amount + currency), без смешивания валют.

Старые записи без amount: для отчёта в RUB берётся COALESCE(pack.prices_by_currency->>'RUB', pack.price);
в USD/EUR такие покупки не учитываются (нет данных о валюте платежа).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Numeric, and_, case, cast, func

from db.models import Pack, Purchase

if TYPE_CHECKING:
    from db.uow import SQLAlchemyUnitOfWork

ADMIN_DISPLAY_CURRENCY_KEY = "admin_display_currency"


async def resolve_revenue_currency(uow: "SQLAlchemyUnitOfWork", explicit: str | None) -> str:
    """Валюта отчёта: query-параметр или настройка admin_display_currency из БД."""
    if explicit:
        c = explicit.strip().upper()
        if c in ("RUB", "USD", "EUR"):
            return c
    raw = await uow.global_setting_repo.get(ADMIN_DISPLAY_CURRENCY_KEY)
    cur = (raw or "RUB").strip().upper()
    if cur not in ("RUB", "USD", "EUR"):
        cur = "RUB"
    return cur


def purchase_revenue_line_expr(revenue_currency: str):
    """Выражение: сколько строка purchase даёт в сумму для выбранной валюты отчёта."""
    cur = (revenue_currency or "RUB").strip().upper()
    if cur not in ("RUB", "USD", "EUR"):
        cur = "RUB"

    currency_norm = func.upper(func.coalesce(Purchase.currency, "RUB"))
    rub_from_pack = func.coalesce(
        cast(Pack.prices_by_currency["RUB"].astext, Numeric(14, 2)),
        cast(Pack.price, Numeric(14, 2)),
    )
    return case(
        (
            and_(Purchase.amount.isnot(None), currency_norm == cur),
            cast(Purchase.amount, Numeric(14, 2)),
        ),
        (
            and_(Purchase.amount.is_(None), cur == "RUB"),
            rub_from_pack,
        ),
        else_=0,
    )
