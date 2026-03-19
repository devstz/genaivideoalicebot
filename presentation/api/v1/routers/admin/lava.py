from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException

from db.models import User
from db.uow import SQLAlchemyUnitOfWork
from presentation.dependencies import get_uow_dependency
from presentation.dependencies.security import get_current_admin
from services.providers.payment.lava_provider import LavaPaymentProvider


lava_router = APIRouter(prefix="/lava", tags=["Admin Lava"])


@lava_router.get("/products")
async def list_lava_products(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    provider = LavaPaymentProvider()
    try:
        data = await provider.list_products()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or str(exc)
        raise HTTPException(status_code=502, detail=f"Lava API error: {detail}")
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Failed to fetch Lava products: {exc}")

    return data
