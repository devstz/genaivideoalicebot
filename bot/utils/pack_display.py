"""Отображение цен паков в боте по языку и валюте."""

from __future__ import annotations

from typing import Any

from db.models import Pack


def _prices_dict(pack: Pack) -> dict[str, float]:
    raw = pack.prices_by_currency
    if not raw or not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in raw.items():
        if v is None:
            continue
        try:
            out[str(k).upper()] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def pick_bot_currency(lang: str) -> str:
    """ru → RUB, иначе (en и др.) → USD."""
    code = (lang or "ru").lower().split("-")[0]
    return "RUB" if code == "ru" else "USD"


def pick_amount_and_currency(pack: Pack, lang: str) -> tuple[float, str]:
    """
    Выбирает сумму и код валюты для отображения.
    Порядок fallback: предпочтительная валюта по языку → RUB → USD → EUR → legacy price.
    """
    prices = _prices_dict(pack)
    preferred = pick_bot_currency(lang)
    order = [preferred, "RUB", "USD", "EUR"]
    seen: set[str] = set()
    for cur in order:
        if cur in seen:
            continue
        seen.add(cur)
        if cur in prices:
            return prices[cur], cur
    if prices:
        k = next(iter(prices))
        return prices[k], k
    return float(pack.price), "RUB"


def format_price_line(amount: float, currency: str) -> str:
    """Одна строка для кнопки / карточки."""
    if currency == "RUB":
        if abs(amount - round(amount)) < 1e-6:
            return f"{int(round(amount))} ₽"
        return f"{amount:.2f} ₽"
    if currency == "USD":
        return f"${amount:.2f}"
    if currency == "EUR":
        return f"{amount:.2f} €"
    return f"{amount:.2f} {currency}"


def pack_price_lines(pack: Pack, lang: str) -> tuple[str, str]:
    """(price_line, per_gen_line) для PACK_DETAILS."""
    amt, cur = pick_amount_and_currency(pack, lang)
    per = amt / pack.generations_count if pack.generations_count else amt
    return format_price_line(amt, cur), format_price_line(per, cur)
