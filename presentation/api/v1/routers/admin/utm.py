"""UTM campaigns and analytics API for admin panel."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError

from db.models import User, UtmCampaign
from db.uow import SQLAlchemyUnitOfWork
from presentation.api.v1.schemas.responeses.utm import (
    UtmCampaignCreate,
    UtmCampaignListResponse,
    UtmCampaignRead,
    UtmCampaignUpdate,
    UtmRegistrationListResponse,
    UtmRegistrationRead,
    UtmSeriesPoint,
    UtmSeriesResponse,
    UtmStatsResponse,
    UtmSummaryResponse,
)
from presentation.dependencies import get_uow_dependency
from presentation.dependencies.security import get_current_admin
from services.utm_service import UtmService

utm_router = APIRouter(prefix="/utm", tags=["Admin UTM"])


@utm_router.get("", response_model=UtmCampaignListResponse)
async def list_utm_campaigns(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    items, total = await UtmService.list_campaigns_with_metrics(
        uow,
        limit=limit,
        offset=offset,
        search=search,
        is_active=is_active,
        from_date=from_date,
        to_date=to_date,
    )
    return UtmCampaignListResponse(
        items=[UtmCampaignRead(**UtmService.campaign_to_dict(campaign, metrics)) for campaign, metrics in items],
        total=total,
    )


@utm_router.post("", response_model=UtmCampaignRead, status_code=201)
async def create_utm_campaign(
    payload: UtmCampaignCreate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    start_code = payload.start_code.strip()
    if not start_code:
        raise HTTPException(status_code=400, detail="start_code is required")

    campaign = UtmCampaign(
        name=payload.name.strip(),
        start_code=start_code,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_content=payload.utm_content,
        utm_term=payload.utm_term,
        is_active=payload.is_active,
    )
    try:
        campaign = await UtmService.create_campaign(uow, campaign)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="start_code already exists")

    metrics = await UtmService.get_metrics_for_campaign(uow, campaign.id)
    return UtmCampaignRead(**UtmService.campaign_to_dict(campaign, metrics))


@utm_router.get("/stats/summary", response_model=UtmSummaryResponse)
async def get_utm_summary(
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    metrics = await UtmService.get_summary_metrics(uow, from_date=from_date, to_date=to_date)
    return UtmSummaryResponse(
        unique_clicks=metrics.unique_clicks,
        new_users=metrics.new_users,
        purchases=metrics.purchases,
        revenue=metrics.revenue,
    )


@utm_router.get("/export.csv")
async def export_utm_campaigns_csv(
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    rows, _ = await UtmService.list_campaigns_with_metrics(
        uow,
        limit=10_000,
        offset=0,
        search=search,
        is_active=is_active,
        from_date=from_date,
        to_date=to_date,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "name",
            "start_code",
            "link",
            "is_active",
            "unique_clicks",
            "registrations",
            "purchases",
            "revenue",
            "created_at",
        ]
    )
    for campaign, metrics in rows:
        writer.writerow(
            [
                campaign.id,
                campaign.name,
                campaign.start_code,
                UtmService._bot_link(campaign.start_code),
                "1" if campaign.is_active else "0",
                metrics.unique_clicks,
                metrics.new_users,
                metrics.purchases,
                metrics.revenue,
                campaign.created_at.isoformat(),
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="utm-campaigns.csv"'},
    )


@utm_router.get("/{campaign_id}", response_model=UtmCampaignRead)
async def get_utm_campaign(
    campaign_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")
    metrics = await UtmService.get_metrics_for_campaign(uow, campaign.id)
    return UtmCampaignRead(**UtmService.campaign_to_dict(campaign, metrics))


@utm_router.put("/{campaign_id}", response_model=UtmCampaignRead)
async def update_utm_campaign(
    campaign_id: int,
    payload: UtmCampaignUpdate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")

    updates: dict[str, object] = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.start_code is not None:
        updates["start_code"] = payload.start_code.strip()
    if payload.utm_source is not None:
        updates["utm_source"] = payload.utm_source
    if payload.utm_medium is not None:
        updates["utm_medium"] = payload.utm_medium
    if payload.utm_campaign is not None:
        updates["utm_campaign"] = payload.utm_campaign
    if payload.utm_content is not None:
        updates["utm_content"] = payload.utm_content
    if payload.utm_term is not None:
        updates["utm_term"] = payload.utm_term
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active

    try:
        if updates:
            await UtmService.update_campaign(uow, campaign, **updates)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="start_code already exists")

    metrics = await UtmService.get_metrics_for_campaign(uow, campaign.id)
    return UtmCampaignRead(**UtmService.campaign_to_dict(campaign, metrics))


@utm_router.delete("/{campaign_id}", status_code=204)
async def delete_utm_campaign(
    campaign_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")
    await UtmService.delete_campaign(uow, campaign)


@utm_router.get("/{campaign_id}/stats", response_model=UtmStatsResponse)
async def get_utm_campaign_stats(
    campaign_id: int,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")

    metrics = await UtmService.get_metrics_for_campaign(uow, campaign_id, from_date=from_date, to_date=to_date)
    conversion = round((metrics.purchases / metrics.unique_clicks) * 100, 2) if metrics.unique_clicks else 0.0
    return UtmStatsResponse(
        unique_clicks=metrics.unique_clicks,
        new_users=metrics.new_users,
        purchases=metrics.purchases,
        revenue=metrics.revenue,
        conversion=conversion,
    )


@utm_router.get("/{campaign_id}/series", response_model=UtmSeriesResponse)
async def get_utm_campaign_series(
    campaign_id: int,
    period: str = Query("day"),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")
    series = await UtmService.get_campaign_series(
        uow,
        campaign_id=campaign_id,
        period=period,
        from_date=from_date,
        to_date=to_date,
    )
    return UtmSeriesResponse(items=[UtmSeriesPoint(**point) for point in series])


@utm_router.get("/{campaign_id}/registrations", response_model=UtmRegistrationListResponse)
async def get_utm_campaign_registrations(
    campaign_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")
    rows, total = await UtmService.get_campaign_registrations(
        uow,
        campaign_id=campaign_id,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
    )
    items = [
        UtmRegistrationRead(
            user_id=user.user_id,
            username=user.username,
            full_name=user.full_name,
            created_at=registration.created_at,
        )
        for registration, user in rows
    ]
    return UtmRegistrationListResponse(items=items, total=total)


@utm_router.get("/{campaign_id}/export.csv")
async def export_utm_campaign_csv(
    campaign_id: int,
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    campaign = await uow.utm_campaign_repo.get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="UTM campaign not found")

    export_data = await UtmService.build_campaign_export_rows(
        uow,
        campaign_id=campaign_id,
        from_date=from_date,
        to_date=to_date,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["campaign_id", campaign.id])
    writer.writerow(["campaign_name", campaign.name])
    writer.writerow(["start_code", campaign.start_code])
    writer.writerow([])
    writer.writerow(["metric", "value"])
    writer.writerow(["unique_clicks", export_data["summary"]["unique_clicks"]])
    writer.writerow(["new_users", export_data["summary"]["new_users"]])
    writer.writerow(["purchases", export_data["summary"]["purchases"]])
    writer.writerow(["revenue", export_data["summary"]["revenue"]])
    writer.writerow([])
    writer.writerow(["user_id", "username", "full_name", "registered_at"])
    for registration in export_data["registrations"]:
        writer.writerow(
            [
                registration["user_id"],
                registration["username"],
                registration["full_name"],
                registration["created_at"],
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="utm-{campaign_id}.csv"'},
    )
