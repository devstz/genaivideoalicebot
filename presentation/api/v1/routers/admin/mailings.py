"""Mailings API for admin panel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.mailing import (
    MailingRead,
    MailingCreate,
    MailingListResponse,
    AudienceStatsResponse,
)
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.mailing import Mailing
from services.mailing_service import send_mailing

mailings_router = APIRouter(prefix="/mailings", tags=["Admin Mailings"])


def _model_to_read(m: Mailing) -> MailingRead:
    return MailingRead(
        id=str(m.id),
        message=m.message,
        audience_filter=m.audience_filter,
        status=m.status,
        recipient_count=m.recipient_count,
        created_at=m.created_at,
        sent_at=m.sent_at,
    )


@mailings_router.get("", response_model=MailingListResponse)
async def list_mailings(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    items, total = await uow.mailing_repo.list_all(limit=limit, offset=offset)
    return MailingListResponse(items=[_model_to_read(m) for m in items], total=total)


@mailings_router.get("/audience-stats", response_model=AudienceStatsResponse)
async def get_audience_stats(
    audience: str = Query("all"),
    include_admins: bool = Query(False),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    count = await uow.user_repo.count_for_audience(audience, include_admins=include_admins)
    total = await uow.user_repo.count_for_audience("all", include_admins=include_admins)
    percent = (count / total * 100) if total else 0
    return AudienceStatsResponse(count=count, total=total, percent=round(percent, 1))


@mailings_router.post("", response_model=MailingRead, status_code=201)
async def create_and_send_mailing(
    payload: MailingCreate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    mailing = Mailing(
        message=payload.message,
        audience_filter=payload.audience,
        status="sending",
        include_admins=payload.include_admins,
    )
    mailing = await uow.mailing_repo.add(mailing)
    await send_mailing(uow, mailing)
    return _model_to_read(mailing)
