from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.user_balance import UserBalance
from db.models.template import Template
from db.models.generation import Generation
import httpx
import math
import logging

from config import get_settings

logger = logging.getLogger(__name__)

dashboard_router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])

# PiAPI Hailuo pricing table (cost in USD)
HAILUO_PRICING = {
    ("v2.3", 6, 768): 0.23,
    ("v2.3", 10, 768): 0.45,
    ("v2.3", 6, 1080): 0.40,
    ("v2.3-fast", 6, 768): 0.16,
    ("v2.3-fast", 10, 768): 0.26,
    ("v2.3-fast", 6, 1080): 0.26,
}

# Current defaults from HailuoGenerator
CURRENT_SUB_MODEL = "v2.3-fast"
CURRENT_DURATION = 6
CURRENT_RESOLUTION = 768


@dashboard_router.get("/metrics")
async def get_dashboard_metrics(
    period: str = "week",
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    from services.metrics_service import MetricsService

    return await MetricsService.get_dashboard_metrics(uow, period=period)


@dashboard_router.get("/piapi-balance")
async def get_piapi_balance(
    admin: User = Depends(get_current_admin),
):
    settings = get_settings()
    api_key = settings.PIAPI_KEY

    cost_per_generation = HAILUO_PRICING.get(
        (CURRENT_SUB_MODEL, CURRENT_DURATION, CURRENT_RESOLUTION), 0.16
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.piapi.ai/account/info",
                headers={"x-api-key": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"PiAPI request failed: {e}")
        return {
            "error": "PiAPI unavailable",
            "balance_usd": None,
            "available_credits": None,
            "used_credits": None,
            "total_credits": None,
            "plan": None,
            "cost_per_generation": cost_per_generation,
            "remaining_generations": None,
            "current_model": f"hailuo {CURRENT_SUB_MODEL}",
            "current_settings": {"duration": CURRENT_DURATION, "resolution": CURRENT_RESOLUTION},
        }

    # Parse PiAPI response
    info = data.get("data", data)
    balance_usd = float(info.get("equivalent_in_usd", 0))
    plan = info.get("plan", "unknown")
    credit_info = info.get("credit_pack_info", {})
    total_credits = int(credit_info.get("total_credits", 0))
    used_credits = int(credit_info.get("used_credits", 0))
    available_credits = int(credit_info.get("available_credits", total_credits - used_credits))

    remaining_generations = math.floor(balance_usd / cost_per_generation) if cost_per_generation > 0 else 0

    return {
        "balance_usd": round(balance_usd, 2),
        "available_credits": available_credits,
        "used_credits": used_credits,
        "total_credits": total_credits,
        "plan": plan,
        "cost_per_generation": cost_per_generation,
        "remaining_generations": remaining_generations,
        "current_model": f"hailuo {CURRENT_SUB_MODEL}",
        "current_settings": {"duration": CURRENT_DURATION, "resolution": CURRENT_RESOLUTION},
    }
