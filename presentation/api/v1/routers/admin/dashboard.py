from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.user_balance import UserBalance
from db.models.template import Template
from db.models.generation import Generation

dashboard_router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])

@dashboard_router.get("/metrics")
async def get_dashboard_metrics(
    period: str = "week",
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin)
):
    from services.metrics_service import MetricsService
    return await MetricsService.get_dashboard_metrics(uow, period=period)
