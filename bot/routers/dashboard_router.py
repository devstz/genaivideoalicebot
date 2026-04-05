import logging
import httpx
import math

from aiogram import F
from aiogram.types import CallbackQuery

from bot.routers.base import BaseRouter
from bot.keyboards.callback_data.private import MainMenuCD
from bot.keyboards.inline.private_keyboards import main_menu_kb, dashboard_kb
from config import get_settings
from db.models import User

logger = logging.getLogger(__name__)

# PiAPI Hailuo pricing table
HAILUO_PRICING = {
    ("v2.3", 6, 768): 0.23,
    ("v2.3", 10, 768): 0.45,
    ("v2.3", 6, 1080): 0.40,
    ("v2.3-fast", 6, 768): 0.16,
    ("v2.3-fast", 10, 768): 0.26,
    ("v2.3-fast", 6, 1080): 0.26,
}
CURRENT_SUB_MODEL = "v2.3-fast"
CURRENT_DURATION = 6
CURRENT_RESOLUTION = 768


class DashboardRouter(BaseRouter):
    def __init__(self) -> None:
        super().__init__()

    def setup_handlers(self) -> None:
        self.callback_query.register(self.show_dashboard, MainMenuCD.filter(F.action == "dashboard"))
        self.callback_query.register(self.refresh_dashboard, MainMenuCD.filter(F.action == "dashboard_refresh"))

    async def _fetch_piapi_balance(self) -> dict:
        settings = get_settings()
        cost = HAILUO_PRICING.get((CURRENT_SUB_MODEL, CURRENT_DURATION, CURRENT_RESOLUTION), 0.16)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.piapi.ai/account/info",
                    headers={"x-api-key": settings.PIAPI_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
            info = data.get("data", data)
            balance = float(info.get("equivalent_in_usd", 0))
            credit_info = info.get("credit_pack_info", {})
            total_credits = int(credit_info.get("total_credits", 0))
            used_credits = int(credit_info.get("used_credits", 0))
            available = int(credit_info.get("available_credits", total_credits - used_credits))
            remaining = math.floor(balance / cost) if cost > 0 else 0
            return {
                "ok": True,
                "balance": balance,
                "total_credits": total_credits,
                "used_credits": used_credits,
                "available_credits": available,
                "remaining": remaining,
                "cost": cost,
            }
        except Exception as e:
            logger.error(f"PiAPI fetch failed: {e}")
            return {"ok": False}

    async def _fetch_metrics(self) -> dict:
        from services.metrics_service import MetricsService
        from db.uow import SQLAlchemyUnitOfWork
        from db.session import SessionFactory

        try:
            uow = SQLAlchemyUnitOfWork(SessionFactory)
            async with uow:
                return await MetricsService.get_dashboard_metrics(uow, period="week")
        except Exception as e:
            logger.error(f"Metrics fetch failed: {e}")
            return None

    async def _build_dashboard_text(self, i18n) -> str:
        metrics = await self._fetch_metrics()
        piapi = await self._fetch_piapi_balance()

        lines = ["\U0001f4ca <b>" + getattr(i18n, 'DASHBOARD_TITLE', 'Дашборд') + "</b>\n"]

        if metrics:
            m = metrics
            total_users = m.get("metrics", {}).get("uniqueUsers", {}).get("value", 0)
            dau = m.get("dau", "?")
            total_gens = m.get("metrics", {}).get("totalGenerations", {}).get("value", 0)
            completed_gens = m.get("completed_generations", "?")

            rev = m.get("metrics", {}).get("revenueMonth", {})
            rev_rub = rev.get("rub", 0)
            rev_usd = rev.get("usd", 0)
            today_rub = rev.get("todayRub", 0)
            today_usd = rev.get("todayUsd", 0)

            lines.append(f"\U0001f465 <b>{getattr(i18n, 'DASHBOARD_USERS', 'Пользователи')}:</b> {total_users:,}")
            lines.append(f"\U0001f3ac <b>{getattr(i18n, 'DASHBOARD_GENERATIONS', 'Генерации')}:</b> {total_gens:,}")
            lines.append("")
            lines.append(f"\U0001f4b0 <b>{getattr(i18n, 'DASHBOARD_REVENUE', 'Выручка за месяц')}:</b>")
            lines.append(f"   \u20bd {rev_rub:,.0f} | $ {rev_usd:,.2f}")
            lines.append(f"   {getattr(i18n, 'DASHBOARD_TODAY', 'Сегодня')}: \u20bd {today_rub:,.0f} | $ {today_usd:,.2f}")

            # Performance
            perf = m.get("performance", {})
            avg_time = perf.get("avgTime", "?")
            status_map = {"stable": "стабильно", "high_load": "нагрузка"}
            perf_status = status_map.get(perf.get("status", ""), perf.get("status", "?"))
            lines.append("")
            lines.append(f"\u26a1 <b>{getattr(i18n, 'DASHBOARD_PERFORMANCE', 'Производительность')}:</b>")
            lines.append(f"   {getattr(i18n, 'DASHBOARD_AVG_TIME', 'Среднее время')}: {avg_time} | {getattr(i18n, 'DASHBOARD_STATUS', 'Статус')}: {perf_status}")

            # Top templates
            top = m.get("topTemplates", [])
            if top:
                lines.append("")
                lines.append(f"\U0001f3c6 <b>{getattr(i18n, 'DASHBOARD_TOP_TEMPLATES', 'Топ шаблоны')}:</b>")
                medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
                for i_t, t in enumerate(top[:3]):
                    medal = medals[i_t] if i_t < 3 else f"{i_t+1}."
                    name = t.get("name", "?")
                    count = t.get("usageCount", 0)
                    rate = t.get("successRate", 0)
                    lines.append(f"{medal} {name} — {count} ({rate}%)")
        else:
            lines.append(f"\u274c {getattr(i18n, 'DASHBOARD_METRICS_UNAVAILABLE', 'Метрики недоступны')}")

        lines.append("")
        if piapi.get("ok"):
            lines.append(f"\U0001f916 <b>PiAPI {getattr(i18n, 'DASHBOARD_BALANCE', 'Баланс')}:</b>")
            lines.append(f"   \U0001f4b5 ${piapi['balance']:.2f} ({getattr(i18n, 'DASHBOARD_CREDITS', 'кредиты')}: {piapi['used_credits']:,}/{piapi['total_credits']:,})")
            lines.append(f"   \U0001f3ac {getattr(i18n, 'DASHBOARD_REMAINING', 'Осталось генераций')}: ~{piapi['remaining']}")
            lines.append(f"   \U0001f4f9 {getattr(i18n, 'DASHBOARD_MODEL', 'Модель')}: hailuo {CURRENT_SUB_MODEL} ({CURRENT_DURATION}s, {CURRENT_RESOLUTION}p)")
        else:
            lines.append(f"\U0001f916 <b>PiAPI:</b> \u274c {getattr(i18n, 'DASHBOARD_PIAPI_UNAVAILABLE', 'PiAPI недоступен')}")

        return "\n".join(lines)

    async def show_dashboard(self, call: CallbackQuery, user: User, i18n) -> None:
        if not user.is_superuser and not user.admin_password_hash:
            await call.answer("Нет прав", show_alert=True)
            return

        await call.answer()
        text = await self._build_dashboard_text(i18n)
        await call.message.edit_text(text, reply_markup=dashboard_kb())

    async def refresh_dashboard(self, call: CallbackQuery, user: User, i18n) -> None:
        if not user.is_superuser and not user.admin_password_hash:
            await call.answer("Нет прав", show_alert=True)
            return

        await call.answer("\U0001f504 Обновление...")
        text = await self._build_dashboard_text(i18n)
        try:
            await call.message.edit_text(text, reply_markup=dashboard_kb())
        except Exception:
            # Message not modified (same content)
            pass
