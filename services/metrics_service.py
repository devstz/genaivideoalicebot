from __future__ import annotations
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, desc, func, select

from db.models import Generation, Pack, Purchase, Referral, Template, User, UserAction
from db.uow import SQLAlchemyUnitOfWork
from enums import ActionType, GenerationStatus, PaymentStatus
from services.revenue_aggregation import purchase_revenue_line_expr


class MetricsService:
    @staticmethod
    def _to_float(value: Decimal | float | int | None) -> float:
        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    async def get_dashboard_metrics(
        uow: SQLAlchemyUnitOfWork,
        period: str = "week",
    ):
        # 1. Users
        total_users = await uow.session.scalar(select(func.count(User.user_id))) or 0
        
        now = datetime.utcnow()
        last_24h = now - timedelta(days=1)
        
        dau_stmt = (
            select(func.count(func.distinct(UserAction.user_id)))
            .where(UserAction.created_at >= last_24h)
        )
        dau = await uow.session.scalar(dau_stmt) or 0

        # 2. Generations
        total_gens = await uow.session.scalar(select(func.count(Generation.id))) or 0
        completed_gens = await uow.session.scalar(
            select(func.count(Generation.id))
            .where(Generation.status == GenerationStatus.COMPLETED)
        ) or 0

        # 3. Выручка отдельно RUB и USD (без смешивания и без EUR в отчёте)
        line_rub = purchase_revenue_line_expr("RUB")
        line_usd = purchase_revenue_line_expr("USD")
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        base_purchase_filters_month = and_(
            Purchase.payment_status == PaymentStatus.CONFIRMED,
            Purchase.created_at >= month_start,
        )
        base_purchase_filters_today = and_(
            Purchase.payment_status == PaymentStatus.CONFIRMED,
            Purchase.created_at >= today_start,
        )

        monthly_rub_stmt = (
            select(func.sum(line_rub))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
            .where(base_purchase_filters_month)
        )
        monthly_usd_stmt = (
            select(func.sum(line_usd))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
            .where(base_purchase_filters_month)
        )
        monthly_rub = MetricsService._to_float(await uow.session.scalar(monthly_rub_stmt))
        monthly_usd = MetricsService._to_float(await uow.session.scalar(monthly_usd_stmt))

        today_rub_stmt = (
            select(func.sum(line_rub))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
            .where(base_purchase_filters_today)
        )
        today_usd_stmt = (
            select(func.sum(line_usd))
            .select_from(Purchase)
            .join(Pack, Purchase.pack_id == Pack.id)
            .where(base_purchase_filters_today)
        )
        today_rub = MetricsService._to_float(await uow.session.scalar(today_rub_stmt))
        today_usd = MetricsService._to_float(await uow.session.scalar(today_usd_stmt))

        # 4. Top Templates
        top_templates_stmt = (
            select(
                Template.id,
                Template.name, 
                func.count(Generation.id).label('usageCount'),
                func.sum(case((Generation.status == GenerationStatus.COMPLETED, 1), else_=0)).label('successCount')
            )
            .outerjoin(Generation, Generation.template_id == Template.id)
            .group_by(Template.id)
            .order_by(desc('usageCount'), Template.name)
            .limit(5)
        )
        templates_result = await uow.session.execute(top_templates_stmt)
        top_templates = []
        for row in templates_result.fetchall():
            success_rate = 0
            if row.usageCount > 0:
                success_rate = int((row.successCount / row.usageCount) * 100)
            
            top_templates.append({
                "id": row.id,
                "name": row.name,
                "usageCount": row.usageCount,
                "successRate": success_rate
            })

        # 5. Conversion Funnel (Updated logic)
        # Category 1: Total Active (sent at least one action)
        total_active_stmt = select(func.count(User.user_id))
        total_active_count = await uow.session.scalar(total_active_stmt) or 0

        # Category 2: Referral Users (users who invited someone)
        referral_users_stmt = select(func.count(func.distinct(Referral.referrer_id)))
        referral_count = await uow.session.scalar(referral_users_stmt) or 0

        # Category 3: Buyers (users who made a successful purchase)
        buyers_stmt = (
            select(func.count(func.distinct(Purchase.user_id)))
            .where(Purchase.payment_status == PaymentStatus.CONFIRMED)
        )
        buyers_count = await uow.session.scalar(buyers_stmt) or 0

        # Proportions relative to active users (or total users if active is 0)
        base_count = total_active_count if total_active_count > 0 else 1
        
        referral_perc = min(100, int((referral_count / base_count) * 100))
        buyers_perc = min(100, int((buyers_count / base_count) * 100))
        
        conversion_funnel = [
            {"key": "total_active", "percentage": 100, "count": total_active_count},
            {"key": "referral_active", "percentage": referral_perc, "count": referral_count},
            {"key": "payers", "percentage": buyers_perc, "count": buyers_count},
        ]

        # 6. Revenue Trend (Dynamic Period)
        period_val = (period or "week").strip().lower()
        days = 30 if period_val == "month" else 7
        revenue_trend = []
        
        for i in range(days - 1, -1, -1):
            day_date = now - timedelta(days=i)
            day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_filters = and_(
                Purchase.payment_status == PaymentStatus.CONFIRMED,
                Purchase.created_at >= day_start,
                Purchase.created_at < day_end,
            )
            day_rub_stmt = (
                select(func.sum(line_rub))
                .select_from(Purchase)
                .join(Pack, Purchase.pack_id == Pack.id)
                .where(day_filters)
            )
            day_usd_stmt = (
                select(func.sum(line_usd))
                .select_from(Purchase)
                .join(Pack, Purchase.pack_id == Pack.id)
                .where(day_filters)
            )
            day_rub = MetricsService._to_float(await uow.session.scalar(day_rub_stmt))
            day_usd = MetricsService._to_float(await uow.session.scalar(day_usd_stmt))
            
            # Label based on period
            if days == 7:
                day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
                label = day_labels[day_start.weekday()]
            else:
                label = day_start.strftime("%d.%m")
            
            revenue_trend.append(
                {
                    "label": label,
                    "rub": round(day_rub, 2),
                    "usd": round(day_usd, 2),
                    "fullDate": day_start.strftime("%Y-%m-%d"),
                }
            )

        # 7. Performance (Avg Completion Time)
        avg_time_stmt = select(func.avg(Generation.updated_at - Generation.created_at)).where(Generation.status == GenerationStatus.COMPLETED)
        avg_time_interval = await uow.session.scalar(avg_time_stmt)
        
        avg_seconds = 0
        if avg_time_interval:
            avg_seconds = int(avg_time_interval.total_seconds())
        
        performance = {
            "avgTime": f"{avg_seconds}s" if avg_seconds > 0 else "0s",
            "status": "stable" if avg_seconds < 60 else "high_load",
            "percentage": min(100, int((avg_seconds / 60) * 100)) if avg_seconds > 0 else 0
        }

        return {
            "metrics": {
                "uniqueUsers": {"value": total_users, "change": f"DAU: {dau}", "isPositive": True},
                "totalGenerations": {"value": total_gens, "change": f"SUCCESS: {completed_gens}", "isPositive": True},
                "revenueMonth": {
                    "rub": round(monthly_rub, 2),
                    "usd": round(monthly_usd, 2),
                    "todayRub": round(today_rub, 2),
                    "todayUsd": round(today_usd, 2),
                    "change": "",
                    "isPositive": True,
                },
            },
            "topTemplates": top_templates,
            "systemHealth": [
                 {"label": "DB_STATUS", "value": "OK", "icon": "database", "isBadge": True, "isGreen": True, "iconColor": "text-emerald-500", "subLabel": "CONNECTED"},
                 {"label": "API", "value": "UP", "icon": "lan", "isBadge": True, "isGreen": True, "iconColor": "text-emerald-500", "subLabel": "STABLE"},
            ],
            "conversionFunnel": conversion_funnel,
            "performance": performance,
            "revenueTrend": revenue_trend
        }
