"""Packs CRUD API for admin panel."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.pack import PackRead, PackCreate, PackUpdate
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.pack import Pack
from services.providers.payment.lava_provider import LavaPaymentProvider

logger = logging.getLogger(__name__)

packs_router = APIRouter(prefix="/packs", tags=["Admin Packs"])


def _normalize_prices(raw: dict[str, Any] | None) -> dict[str, float]:
    out: dict[str, float] = {}
    if not raw:
        return out
    for k, v in raw.items():
        if v is None:
            continue
        try:
            out[str(k).upper()] = float(v)
        except (TypeError, ValueError):
            continue
    return out


async def _prices_from_lava(lava_offer_id: str | None) -> dict[str, float] | None:
    if not lava_offer_id:
        return None
    try:
        provider = LavaPaymentProvider()
        return await provider.get_offer_prices_by_currency(lava_offer_id)
    except Exception as exc:
        logger.warning("Failed to fetch Lava prices for offer %s: %s", lava_offer_id, exc)
        return None


def _merge_prices(
    base: dict[str, float],
    from_lava: dict[str, float] | None,
    *,
    lava_offer_id: str | None,
) -> dict[str, float]:
    merged = dict(base)
    if lava_offer_id and from_lava:
        merged.update(from_lava)
    return merged


def _price_rub_column(prices: dict[str, float], fallback: float) -> float:
    return float(prices.get("RUB", fallback))


def _model_to_read(p: Pack) -> PackRead:
    return PackRead(
        id=str(p.id),
        name=p.name,
        description=p.description or "",
        generations_count=p.generations_count,
        price=float(p.price),
        prices_by_currency=p.prices_by_currency if isinstance(p.prices_by_currency, dict) else None,
        icon=p.icon,
        is_active=p.is_active,
        is_bestseller=p.is_bestseller,
        lava_offer_id=p.lava_offer_id,
        created_at=p.created_at,
    )


@packs_router.get("", response_model=list[PackRead])
async def list_packs(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    packs = await uow.pack_repo.list_all()
    return [_model_to_read(p) for p in packs]


@packs_router.get("/{pack_id}", response_model=PackRead)
async def get_pack(
    pack_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    pack = await uow.pack_repo.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return _model_to_read(pack)


@packs_router.post("", response_model=PackRead, status_code=201)
async def create_pack(
    payload: PackCreate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    lava_offer_id = payload.lava_offer_id or None
    manual = _normalize_prices(payload.prices_by_currency)
    if not manual:
        manual = {"RUB": float(payload.price)}

    lava_prices = await _prices_from_lava(lava_offer_id)
    prices = _merge_prices(manual, lava_prices, lava_offer_id=lava_offer_id)
    price_col = _price_rub_column(prices, float(payload.price))

    pack = Pack(
        name=payload.name,
        description=payload.description or None,
        generations_count=payload.generations_count,
        price=price_col,
        prices_by_currency=prices or None,
        icon=payload.icon or "payments",
        is_active=payload.is_active if payload.is_active is not None else True,
        is_bestseller=payload.is_bestseller or False,
        lava_offer_id=lava_offer_id,
    )
    pack = await uow.pack_repo.add(pack)
    return _model_to_read(pack)


@packs_router.put("/{pack_id}", response_model=PackRead)
async def update_pack(
    pack_id: int,
    payload: PackUpdate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    pack = await uow.pack_repo.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")

    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.generations_count is not None:
        updates["generations_count"] = payload.generations_count
    if payload.icon is not None:
        updates["icon"] = payload.icon
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
    if payload.is_bestseller is not None:
        updates["is_bestseller"] = payload.is_bestseller
    if payload.lava_offer_id is not None:
        updates["lava_offer_id"] = payload.lava_offer_id or None

    current_prices = _normalize_prices(pack.prices_by_currency if isinstance(pack.prices_by_currency, dict) else None)
    if not current_prices:
        current_prices = {"RUB": float(pack.price)}

    if payload.prices_by_currency is not None:
        current_prices = _normalize_prices(payload.prices_by_currency)

    if payload.price is not None:
        current_prices["RUB"] = float(payload.price)

    new_offer_id = updates.get("lava_offer_id", pack.lava_offer_id)
    lava_prices = await _prices_from_lava(new_offer_id)
    merged = _merge_prices(current_prices, lava_prices, lava_offer_id=new_offer_id)
    updates["prices_by_currency"] = merged
    updates["price"] = _price_rub_column(merged, float(pack.price))

    if updates:
        await uow.pack_repo.update(pack, **updates)

    return _model_to_read(pack)


@packs_router.patch("/{pack_id}/toggle", response_model=PackRead)
async def toggle_pack(
    pack_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    pack = await uow.pack_repo.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    await uow.pack_repo.update(pack, is_active=not pack.is_active)
    return _model_to_read(pack)


@packs_router.delete("/{pack_id}", status_code=204)
async def delete_pack(
    pack_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    pack = await uow.pack_repo.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    uow.pack_repo.delete(pack)
