"""Templates CRUD API for admin panel."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.template import TemplateRead, TemplateCreate, TemplateUpdate
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.template import Template
from enums import TemplateStatus
from config.settings import get_settings

templates_router = APIRouter(prefix="/templates", tags=["Admin Templates"])

def _reject_data_url(field_name: str, value: Optional[str]) -> None:
    if value is not None and value.startswith("data:"):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}: загрузите файл через POST /admin/templates/upload, не передавайте data URL в JSON.",
        )

import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, File

def _model_to_read(t: Template) -> TemplateRead:
    image = ""
    if t.preview_image_path:
        if t.preview_image_path.startswith("http"):
            image = t.preview_image_path
        elif t.preview_image_path.startswith("/"):
            image = t.preview_image_path
        else:
            image = f"/media/{t.preview_image_path}"
    video = None
    if t.preview_video_path:
        if t.preview_video_path.startswith("http"):
            video = t.preview_video_path
        elif t.preview_video_path.startswith("/"):
            video = t.preview_video_path
        else:
            video = f"/media/{t.preview_video_path}"
    return TemplateRead(
        id=str(t.id),
        title=t.name,
        description=t.base_prompt,
        category=t.category,
        status=t.status.value if hasattr(t.status, "value") else str(t.status),
        image=image,
        video=video,
        negativePrompt=t.negative_prompt,
        templateType=getattr(t, "template_type", "preset") or "preset",
    )

@templates_router.post("/upload")
async def upload_template_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
):
    settings = get_settings()
    media_dir = Path(settings.MEDIA_ROOT) / "templates"
    media_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(file.filename).suffix if file.filename else ""
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = media_dir / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"path": f"templates/{filename}"}


@templates_router.get("", response_model=list[TemplateRead])
async def list_templates(
    template_type: Optional[str] = Query(None, alias="templateType"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    if template_type:
        templates = await uow.template_repo.list_all_by_type(template_type)
    else:
        templates = await uow.template_repo.list_all()
    return [_model_to_read(t) for t in templates]


@templates_router.get("/categories", response_model=list[str])
async def list_categories(
    template_type: Optional[str] = Query(None, alias="templateType"),
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    if template_type:
        categories = await uow.template_repo.list_distinct_categories_by_type(template_type)
    else:
        categories = await uow.template_repo.list_distinct_categories()
    return categories or ["face", "motion", "animals", "scene"]


@templates_router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    template = await uow.template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _model_to_read(template)


@templates_router.post("", response_model=TemplateRead, status_code=201)
async def create_template(
    payload: TemplateCreate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    _reject_data_url("image", payload.image)
    _reject_data_url("video", payload.video)
    ai_model = await uow.ai_model_repo.get_current()
    if not ai_model:
        ai_models = await uow.ai_model_repo.list_all()
        if not ai_models:
            raise HTTPException(status_code=400, detail="No AI model found. Run seed.py first.")
        ai_model = ai_models[0]

    status_val = payload.status
    try:
        status_enum = TemplateStatus(status_val)
    except ValueError:
        status_enum = TemplateStatus.HIDDEN

    template = Template(
        name=payload.title,
        category=payload.category,
        base_prompt=payload.description,
        negative_prompt=payload.negativePrompt,
        status=status_enum,
        preview_image_path=payload.image,
        preview_video_path=payload.video,
        ai_model_id=ai_model.id,
        template_type=payload.templateType or "preset",
    )
    template = await uow.template_repo.add(template)
    return _model_to_read(template)


@templates_router.put("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: int,
    payload: TemplateUpdate,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    template = await uow.template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    _reject_data_url("image", payload.image)
    _reject_data_url("video", payload.video)

    if payload.title is not None:
        template.name = payload.title
    if payload.description is not None:
        template.base_prompt = payload.description
    if payload.category is not None:
        template.category = payload.category
    if payload.status is not None:
        try:
            template.status = TemplateStatus(payload.status)
        except ValueError:
            pass
    if payload.image is not None:
        template.preview_image_path = payload.image
    if payload.video is not None:
        template.preview_video_path = payload.video
    if payload.negativePrompt is not None:
        template.negative_prompt = payload.negativePrompt
    if payload.templateType is not None:
        template.template_type = payload.templateType

    await uow.session.flush()
    return _model_to_read(template)


@templates_router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    template = await uow.template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await uow.template_repo.delete(template)
