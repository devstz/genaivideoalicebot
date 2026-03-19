from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select

from config.settings import get_settings
from db.models import Pack, Purchase, User, UtmCampaign, UtmClick, UtmRegistration
from db.uow import SQLAlchemyUnitOfWork
from enums import PaymentStatus
from services.revenue_aggregation import purchase_revenue_line_expr


@dataclass
class UtmMetrics:
    unique_clicks: int = 0
    new_users: int = 0
    purchases: int = 0
    revenue_rub: float = 0.0
    revenue_usd: float = 0.0


class UtmService:
    @staticmethod
    def _to_float(value: Decimal | float | int | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _bot_link(start_code: str) -> str:
        settings = get_settings()
        bot_username = settings.BOT_USERNAME.replace("@", "") if settings.BOT_USERNAME else "bot"
        return f"https://t.me/{bot_username}?start={start_code}"

    @staticmethod
    def _date_bounds(
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        def _ensure_tz(value: datetime | None) -> datetime | None:
            if value is None:
                return None
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        return _ensure_tz(from_date), _ensure_tz(to_date)

    @staticmethod
    async def _sum_revenue_rub_usd(
        uow: SQLAlchemyUnitOfWork,
        purchase_where,
        *,
        join_utm_registration: bool,
    ) -> tuple[float, float]:
        line_rub = purchase_revenue_line_expr("RUB")
        line_usd = purchase_revenue_line_expr("USD")
        rub_from = (
            select(func.sum(line_rub))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
        )
        usd_from = (
            select(func.sum(line_usd))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
        )
        if join_utm_registration:
            rub_from = rub_from.join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
            usd_from = usd_from.join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
        rub_stmt = rub_from.where(purchase_where)
        usd_stmt = usd_from.where(purchase_where)
        rub = UtmService._to_float(await uow.session.scalar(rub_stmt))
        usd = UtmService._to_float(await uow.session.scalar(usd_stmt))
        return rub, usd

    @staticmethod
    async def get_metrics_for_campaign(
        uow: SQLAlchemyUnitOfWork,
        campaign_id: int,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> UtmMetrics:
        from_date, to_date = UtmService._date_bounds(from_date, to_date)

        clicks_filters = [UtmClick.utm_campaign_id == campaign_id]
        regs_filters = [UtmRegistration.utm_campaign_id == campaign_id]
        purchase_filters = [
            UtmRegistration.utm_campaign_id == campaign_id,
            Purchase.payment_status == PaymentStatus.CONFIRMED,
        ]
        if from_date is not None:
            clicks_filters.append(UtmClick.created_at >= from_date)
            regs_filters.append(UtmRegistration.created_at >= from_date)
            purchase_filters.append(Purchase.created_at >= from_date)
        if to_date is not None:
            clicks_filters.append(UtmClick.created_at <= to_date)
            regs_filters.append(UtmRegistration.created_at <= to_date)
            purchase_filters.append(Purchase.created_at <= to_date)

        clicks_stmt = select(func.count(UtmClick.id)).where(and_(*clicks_filters))
        regs_stmt = select(func.count(UtmRegistration.id)).where(and_(*regs_filters))
        purchases_stmt = (
            select(func.count(Purchase.id))
            .join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
            .where(and_(*purchase_filters))
        )
        purchase_where = and_(*purchase_filters)
        revenue_rub, revenue_usd = await UtmService._sum_revenue_rub_usd(
            uow,
            purchase_where,
            join_utm_registration=True,
        )

        unique_clicks = int(await uow.session.scalar(clicks_stmt) or 0)
        new_users = int(await uow.session.scalar(regs_stmt) or 0)
        purchases = int(await uow.session.scalar(purchases_stmt) or 0)
        return UtmMetrics(
            unique_clicks=unique_clicks,
            new_users=new_users,
            purchases=purchases,
            revenue_rub=revenue_rub,
            revenue_usd=revenue_usd,
        )

    @staticmethod
    async def get_summary_metrics(
        uow: SQLAlchemyUnitOfWork,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> UtmMetrics:
        from_date, to_date = UtmService._date_bounds(from_date, to_date)
        clicks_filters = []
        regs_filters = []
        purchase_filters = [Purchase.payment_status == PaymentStatus.CONFIRMED]
        if from_date is not None:
            clicks_filters.append(UtmClick.created_at >= from_date)
            regs_filters.append(UtmRegistration.created_at >= from_date)
            purchase_filters.append(Purchase.created_at >= from_date)
        if to_date is not None:
            clicks_filters.append(UtmClick.created_at <= to_date)
            regs_filters.append(UtmRegistration.created_at <= to_date)
            purchase_filters.append(Purchase.created_at <= to_date)

        clicks_stmt = select(func.count(UtmClick.id)).where(and_(*clicks_filters)) if clicks_filters else select(func.count(UtmClick.id))
        regs_stmt = (
            select(func.count(UtmRegistration.id)).where(and_(*regs_filters))
            if regs_filters
            else select(func.count(UtmRegistration.id))
        )
        purchases_stmt = (
            select(func.count(Purchase.id))
            .join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
            .where(and_(*purchase_filters))
        )
        purchase_where = and_(*purchase_filters)
        revenue_rub, revenue_usd = await UtmService._sum_revenue_rub_usd(
            uow,
            purchase_where,
            join_utm_registration=True,
        )

        unique_clicks = int(await uow.session.scalar(clicks_stmt) or 0)
        new_users = int(await uow.session.scalar(regs_stmt) or 0)
        purchases = int(await uow.session.scalar(purchases_stmt) or 0)
        return UtmMetrics(
            unique_clicks=unique_clicks,
            new_users=new_users,
            purchases=purchases,
            revenue_rub=revenue_rub,
            revenue_usd=revenue_usd,
        )

    @staticmethod
    async def list_campaigns_with_metrics(
        uow: SQLAlchemyUnitOfWork,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        is_active: bool | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[tuple[UtmCampaign, UtmMetrics]], int]:
        items = await uow.utm_campaign_repo.list(
            limit=limit,
            offset=offset,
            search=search,
            is_active=is_active,
            from_date=from_date,
            to_date=to_date,
        )
        total = await uow.utm_campaign_repo.count(
            search=search,
            is_active=is_active,
            from_date=from_date,
            to_date=to_date,
        )
        result: list[tuple[UtmCampaign, UtmMetrics]] = []
        for item in items:
            metrics = await UtmService.get_metrics_for_campaign(
                uow,
                item.id,
                from_date=from_date,
                to_date=to_date,
            )
            result.append((item, metrics))
        return result, total

    @staticmethod
    async def create_campaign(uow: SQLAlchemyUnitOfWork, campaign: UtmCampaign) -> UtmCampaign:
        return await uow.utm_campaign_repo.add(campaign)

    @staticmethod
    async def update_campaign(uow: SQLAlchemyUnitOfWork, campaign: UtmCampaign, **kwargs: object) -> UtmCampaign:
        return await uow.utm_campaign_repo.update(campaign, **kwargs)

    @staticmethod
    async def delete_campaign(uow: SQLAlchemyUnitOfWork, campaign: UtmCampaign) -> None:
        await uow.utm_campaign_repo.delete(campaign)

    @staticmethod
    async def get_campaign_registrations(
        uow: SQLAlchemyUnitOfWork,
        *,
        campaign_id: int,
        limit: int,
        offset: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[tuple[UtmRegistration, User]], int]:
        from_date, to_date = UtmService._date_bounds(from_date, to_date)
        filters = [UtmRegistration.utm_campaign_id == campaign_id]
        if from_date is not None:
            filters.append(UtmRegistration.created_at >= from_date)
        if to_date is not None:
            filters.append(UtmRegistration.created_at <= to_date)

        total_stmt = select(func.count(UtmRegistration.id)).where(and_(*filters))
        total = int(await uow.session.scalar(total_stmt) or 0)

        stmt = (
            select(UtmRegistration, User)
            .join(User, User.user_id == UtmRegistration.user_id)
            .where(and_(*filters))
            .order_by(UtmRegistration.created_at.desc(), UtmRegistration.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await uow.session.execute(stmt)
        return list(result.all()), total

    @staticmethod
    async def get_campaign_series(
        uow: SQLAlchemyUnitOfWork,
        *,
        campaign_id: int,
        period: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict]:
        period_value = (period or "day").strip().lower()
        now = datetime.now(timezone.utc)
        from_date, to_date = UtmService._date_bounds(from_date, to_date)
        line_rub = purchase_revenue_line_expr("RUB")
        line_usd = purchase_revenue_line_expr("USD")

        if period_value == "month":
            step = timedelta(days=30)
            label_fmt = "%m.%Y"
            default_points = 12
        elif period_value == "week":
            step = timedelta(days=7)
            label_fmt = "%d.%m"
            default_points = 8
        else:
            step = timedelta(days=1)
            label_fmt = "%d.%m"
            default_points = 14

        range_end = to_date or now
        if from_date is not None:
            range_start = from_date
        else:
            range_start = range_end - (step * (default_points - 1))
        range_start = range_start.replace(hour=0, minute=0, second=0, microsecond=0)
        if range_end < range_start:
            range_end = range_start

        period_starts: list[datetime] = []
        cursor = range_start
        max_points = 180
        while cursor <= range_end and len(period_starts) < max_points:
            period_starts.append(cursor)
            cursor += step

        series: list[dict] = []
        for period_start in period_starts:
            period_end = min(period_start + step, range_end + timedelta(microseconds=1))

            clicks_stmt = select(func.count(UtmClick.id)).where(
                and_(
                    UtmClick.utm_campaign_id == campaign_id,
                    UtmClick.created_at >= period_start,
                    UtmClick.created_at < period_end,
                )
            )
            regs_stmt = select(func.count(UtmRegistration.id)).where(
                and_(
                    UtmRegistration.utm_campaign_id == campaign_id,
                    UtmRegistration.created_at >= period_start,
                    UtmRegistration.created_at < period_end,
                )
            )
            purchases_stmt = (
                select(func.count(Purchase.id))
                .join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
                .where(
                    and_(
                        UtmRegistration.utm_campaign_id == campaign_id,
                        Purchase.payment_status == PaymentStatus.CONFIRMED,
                        Purchase.created_at >= period_start,
                        Purchase.created_at < period_end,
                    )
                )
            )
            period_purchase_where = and_(
                UtmRegistration.utm_campaign_id == campaign_id,
                Purchase.payment_status == PaymentStatus.CONFIRMED,
                Purchase.created_at >= period_start,
                Purchase.created_at < period_end,
            )
            rub_stmt = (
                select(func.sum(line_rub))
                .select_from(Purchase)
                .join(Pack, Purchase.pack_id == Pack.id)
                .join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
                .where(period_purchase_where)
            )
            usd_stmt = (
                select(func.sum(line_usd))
                .select_from(Purchase)
                .join(Pack, Purchase.pack_id == Pack.id)
                .join(UtmRegistration, UtmRegistration.user_id == Purchase.user_id)
                .where(period_purchase_where)
            )

            clicks = int(await uow.session.scalar(clicks_stmt) or 0)
            regs = int(await uow.session.scalar(regs_stmt) or 0)
            purchases = int(await uow.session.scalar(purchases_stmt) or 0)
            revenue_rub = UtmService._to_float(await uow.session.scalar(rub_stmt))
            revenue_usd = UtmService._to_float(await uow.session.scalar(usd_stmt))

            series.append(
                {
                    "label": period_start.strftime(label_fmt),
                    "full_date": period_start.strftime("%Y-%m-%d"),
                    "clicks": clicks,
                    "registrations": regs,
                    "purchases": purchases,
                    "revenue_rub": revenue_rub,
                    "revenue_usd": revenue_usd,
                }
            )

        return series

    @staticmethod
    async def build_campaign_export_rows(
        uow: SQLAlchemyUnitOfWork,
        *,
        campaign_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict:
        metrics = await UtmService.get_metrics_for_campaign(
            uow,
            campaign_id,
            from_date=from_date,
            to_date=to_date,
        )
        rows, _ = await UtmService.get_campaign_registrations(
            uow,
            campaign_id=campaign_id,
            limit=10_000,
            offset=0,
            from_date=from_date,
            to_date=to_date,
        )
        registrations = [
            {
                "user_id": user.user_id,
                "username": user.username or "",
                "full_name": user.full_name or "",
                "created_at": registration.created_at.isoformat(),
            }
            for registration, user in rows
        ]
        return {
            "summary": {
                "unique_clicks": metrics.unique_clicks,
                "new_users": metrics.new_users,
                "purchases": metrics.purchases,
                "revenue_rub": metrics.revenue_rub,
                "revenue_usd": metrics.revenue_usd,
            },
            "registrations": registrations,
        }

    @staticmethod
    async def resolve_campaign_by_start_code(
        uow: SQLAlchemyUnitOfWork,
        *,
        start_code: str,
    ) -> UtmCampaign | None:
        campaign = await uow.utm_campaign_repo.get_by_start_code(start_code)
        if not campaign or not campaign.is_active:
            return None
        return campaign

    @staticmethod
    async def track_click_if_new(
        uow: SQLAlchemyUnitOfWork,
        *,
        campaign_id: int,
        user_id: int,
    ) -> bool:
        exists = await uow.utm_click_repo.exists_for_user(campaign_id=campaign_id, user_id=user_id)
        if exists:
            return False
        await uow.utm_click_repo.add(UtmClick(utm_campaign_id=campaign_id, user_id=user_id))
        return True

    @staticmethod
    async def track_registration_if_new(
        uow: SQLAlchemyUnitOfWork,
        *,
        campaign_id: int,
        user_id: int,
    ) -> bool:
        exists = await uow.utm_registration_repo.exists_for_user(campaign_id=campaign_id, user_id=user_id)
        if exists:
            return False
        await uow.utm_registration_repo.add(UtmRegistration(utm_campaign_id=campaign_id, user_id=user_id))
        return True

    @staticmethod
    def campaign_to_dict(campaign: UtmCampaign, metrics: UtmMetrics) -> dict:
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "start_code": campaign.start_code,
            "link": UtmService._bot_link(campaign.start_code),
            "utm_source": campaign.utm_source,
            "utm_medium": campaign.utm_medium,
            "utm_campaign": campaign.utm_campaign,
            "utm_content": campaign.utm_content,
            "utm_term": campaign.utm_term,
            "is_active": campaign.is_active,
            "created_at": campaign.created_at,
            "unique_clicks": metrics.unique_clicks,
            "registrations": metrics.new_users,
            "purchases": metrics.purchases,
            "revenue_rub": metrics.revenue_rub,
            "revenue_usd": metrics.revenue_usd,
        }
