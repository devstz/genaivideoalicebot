"""Packs CRUD API for admin panel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.pack import PackRead, PackCreate, PackUpdate
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.pack import Pack

packs_router = APIRouter(prefix="/packs", tags=["Admin Packs"])


def _model_to_read(p: Pack) -> PackRead:
    return PackRead(
        id=str(p.id),
        name=p.name,
        description=p.description or "",
        generations_count=p.generations_count,
        price=float(p.price),
        icon=p.icon,
        is_active=p.is_active,
        is_bestseller=p.is_bestseller,
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
    pack = Pack(
        name=payload.name,
        description=payload.description or None,
        generations_count=payload.generations_count,
        price=payload.price,
        icon=payload.icon or "payments",
        is_active=payload.is_active if payload.is_active is not None else True,
        is_bestseller=payload.is_bestseller or False,
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

    updates = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.generations_count is not None:
        updates["generations_count"] = payload.generations_count
    if payload.price is not None:
        updates["price"] = payload.price
    if payload.icon is not None:
        updates["icon"] = payload.icon
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
    if payload.is_bestseller is not None:
        updates["is_bestseller"] = payload.is_bestseller

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
