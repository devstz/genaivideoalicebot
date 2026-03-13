"""Templates CRUD API for admin panel."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from presentation.dependencies.security import get_current_admin
from presentation.dependencies import get_uow_dependency
from presentation.api.v1.schemas.responeses.template import TemplateRead, TemplateCreate, TemplateUpdate
from db.uow import SQLAlchemyUnitOfWork
from db.models.user import User
from db.models.template import Template
from enums import TemplateStatus
from config.settings import get_settings

templates_router = APIRouter(prefix="/templates", tags=["Admin Templates"])

DEFAULT_IMAGE = "https://lh3.googleusercontent.com/aida-public/AB6AXuAGk5jAQZWsx1pwKk1ZfnRDTArPKzDzQofsxwX4xZDzAGBazgkACgh7tLlFq_PFXd7b31vyhmgdAk5GMhBSHtgvL-01i8k08jExi8rfFMimJXO2yaohNICK__ZDGzkr2g8yy3CH9IaL8EvbqQ-yTHAeCLBX6q3D-NWOd3nF7GBkSK5M-mlB0KdCoitGqaNl_6YA0QKBESbJXLD8nKLenXV-lyJCidLO152JT_nGbSvaqdrwYh_yIiA36g3lXA-mEclY96y9beGBhA"


def _model_to_read(t: Template) -> TemplateRead:
    image = t.preview_image_path or DEFAULT_IMAGE
    if t.preview_image_path and not t.preview_image_path.startswith("http"):
        settings = get_settings()
        image = f"/media/{t.preview_image_path}" if t.preview_image_path else DEFAULT_IMAGE
    return TemplateRead(
        id=str(t.id),
        title=t.name,
        description=t.base_prompt,
        category=t.category,
        status=t.status.value if hasattr(t.status, "value") else str(t.status),
        image=image,
        negativePrompt=t.negative_prompt,
    )


@templates_router.get("", response_model=list[TemplateRead])
async def list_templates(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
    templates = await uow.template_repo.list_all()
    return [_model_to_read(t) for t in templates]


@templates_router.get("/categories", response_model=list[str])
async def list_categories(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow_dependency),
    admin: User = Depends(get_current_admin),
):
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
        ai_model_id=ai_model.id,
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
    if payload.negativePrompt is not None:
        template.negative_prompt = payload.negativePrompt

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
