"""Generations (logs) API for admin panel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.generation import GenerationLogRead, GenerationLogListResponse
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.generation import Generation
from enums import GenerationStatus
from config.settings import get_settings

generations_router = APIRouter(prefix="/generations", tags=["Admin Generations"])


def _build_media_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return f"/media/{path}"


def _model_to_read(g: Generation) -> GenerationLogRead:
    status_val = g.status.value if hasattr(g.status, "value") else str(g.status)
    # Map backend statuses to frontend labels
    status_map = {
        GenerationStatus.PENDING.value: "pending",
        GenerationStatus.PROCESSING.value: "processing",
        GenerationStatus.COMPLETED.value: "completed",
        GenerationStatus.FAILED.value: "failed",
    }
    status_str = status_map.get(status_val, status_val)

    source_image_path = (
        f"{g.media_folder}/photo.jpg"
        if g.media_folder
        else g.input_photo_path
    )

    return GenerationLogRead(
        id=f"GEN-{g.id:05d}",
        created_at=g.created_at,
        source_image_url=_build_media_url(source_image_path),
        user_prompt=g.user_prompt,
        result_video_url=_build_media_url(g.result_video_path) if g.result_video_path else None,
        status=status_str,
        error_message=g.error_message,
    )


@generations_router.get("", response_model=GenerationLogListResponse)
async def list_generations(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    items, total = await uow.generation_repo.list_for_admin(
        limit=limit,
        offset=offset,
        status=status,
    )
    return GenerationLogListResponse(
        items=[_model_to_read(g) for g in items],
        total=total,
    )
