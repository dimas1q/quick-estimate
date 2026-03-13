# backend/app/api/templates.py
# Implementation of the templates API endpoints

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import ValidationError
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.item import EstimateItem
from app.models.template import EstimateTemplate
from app.schemas.paginated import Paginated
from app.schemas.template import (
    EstimateTemplateCreate,
    EstimateTemplateOut,
    TemplateImportPreviewOut,
    TemplateImportRequest,
    TemplateImportSummary,
)
from app.services.audit_ledger import append_audit_ledger_entry
from app.utils.auth import get_current_user
from app.utils.workspace import (
    WORKSPACE_PERMISSION_DATA_EDIT,
    WORKSPACE_PERMISSION_DATA_VIEW,
    WorkspaceContext,
    require_workspace_permission,
)

router = APIRouter(tags=["templates"], dependencies=[Depends(get_current_user)])

ALLOWED_UNITS = {
    "шт",
    "час",
    "день",
    "м²",
    "м",
    "чел.",
    "комп.",
    "усл.",
    "чел/час",
    "чел/смена",
    "проект",
    "пог.м",
    "рейс",
    "машина",
}


def _format_loc(loc: tuple[Any, ...]) -> str:
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            if path:
                path += "."
            path += str(part)
    return path or "payload"


def _normalize_template_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    normalized: dict[str, Any] = {
        "name": payload.get("name", ""),
        "description": payload.get("description"),
        "use_internal_price": payload.get("use_internal_price", True),
        "items": payload.get("items", []),
    }

    if "id" in payload:
        warnings.append("Поле id в шаблоне проигнорировано при импорте")

    if isinstance(normalized["items"], list):
        normalized_items: list[dict[str, Any]] = []
        ignored_item_ids = False
        for item in normalized["items"]:
            if not isinstance(item, dict):
                normalized_items.append(item)
                continue

            item_payload = dict(item)
            if "id" in item_payload:
                ignored_item_ids = True
                item_payload.pop("id", None)

            if (
                (not item_payload.get("category"))
                and item_payload.get("category_input")
            ):
                item_payload["category"] = item_payload.get("category_input")

            item_payload.pop("category_input", None)
            normalized_items.append(item_payload)

        if ignored_item_ids:
            warnings.append("Поля id в позициях шаблона проигнорированы")

        normalized["items"] = normalized_items

    return normalized, warnings


def _validate_units(payload: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    items = payload.get("items")
    if not isinstance(items, list):
        return errors

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        unit = item.get("unit")
        if unit is None:
            continue
        if str(unit) not in ALLOWED_UNITS:
            errors.append(
                {
                    "path": f"items[{i}].unit",
                    "message": (
                        f"Недопустимая единица измерения: '{unit}'. "
                        f"Разрешено: {', '.join(sorted(ALLOWED_UNITS))}"
                    ),
                }
            )
    return errors


async def _build_import_preview(
    payload: dict[str, Any],
    db: AsyncSession,
    context: WorkspaceContext | Any,
) -> TemplateImportPreviewOut:
    if not isinstance(payload, dict):
        return TemplateImportPreviewOut(
            valid=False,
            errors=[{"path": "payload", "message": "Ожидается JSON-объект шаблона"}],
        )

    normalized, warnings = _normalize_template_payload(payload)
    errors = _validate_units(normalized)

    template_data = None
    try:
        template_data = EstimateTemplateCreate.model_validate(normalized)
    except ValidationError as exc:
        errors.extend(
            [
                {"path": _format_loc(err.get("loc", tuple())), "message": err.get("msg", "Неверное значение")}
                for err in exc.errors()
            ]
        )

    if errors or template_data is None:
        return TemplateImportPreviewOut(valid=False, errors=errors, warnings=warnings)

    org_id = getattr(context, "organization_id", None)
    user_id = getattr(context, "id", None)
    uniqueness_filters = [EstimateTemplate.name == template_data.name]
    if org_id is not None:
        uniqueness_filters.append(EstimateTemplate.organization_id == org_id)
    elif user_id is not None:
        # Backward compatibility for legacy tests that pass plain user object.
        uniqueness_filters.append(EstimateTemplate.user_id == user_id)

    name_exists = bool(
        await db.scalar(
            select(func.count())
            .select_from(EstimateTemplate)
            .where(*uniqueness_filters)
        )
    )
    if name_exists:
        warnings.append("Шаблон с таким названием уже существует")

    categories = sorted(
        {item.category.strip() for item in template_data.items if item.category and item.category.strip()}
    )
    summary = TemplateImportSummary(
        name=template_data.name,
        item_count=len(template_data.items),
        category_count=len(categories),
        categories=categories,
        name_exists=name_exists,
    )
    return TemplateImportPreviewOut(
        valid=True,
        errors=[],
        warnings=warnings,
        preview=template_data,
        summary=summary,
    )


async def _create_template_from_payload(
    template: EstimateTemplateCreate,
    db: AsyncSession,
    context: WorkspaceContext,
) -> EstimateTemplate:
    user = context.user
    new_template = EstimateTemplate(
        name=template.name,
        description=template.description,
        use_internal_price=template.use_internal_price,
        user_id=user.id,
        organization_id=context.organization_id,
    )
    db.add(new_template)
    await db.flush()

    for item in template.items:
        db.add(EstimateItem(**item.model_dump(), template_id=new_template.id))

    await db.commit()

    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == new_template.id)
    )
    return result.scalar_one()


@router.post("/", response_model=EstimateTemplateOut)
async def create_template(
    template: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    return await _create_template_from_payload(template, db, context)


@router.get("/", response_model=Paginated[EstimateTemplateOut])
async def list_templates(
    name: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    filters = [EstimateTemplate.organization_id == context.organization_id]

    if name:
        filters.append(EstimateTemplate.name.ilike(f"%{name}%"))
    count_q = select(func.count()).select_from(EstimateTemplate).where(*filters)
    total = await db.scalar(count_q)

    query = (
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(*filters)
        .order_by(EstimateTemplate.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(query)
    return {"items": result.scalars().all(), "total": total}


@router.post("/import/preview", response_model=TemplateImportPreviewOut)
async def preview_template_import(
    request: TemplateImportRequest,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    return await _build_import_preview(request.payload, db, context)


@router.post("/import", response_model=EstimateTemplateOut, status_code=status.HTTP_201_CREATED)
async def import_template(
    request: TemplateImportRequest,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    preview = await _build_import_preview(request.payload, db, context)
    if not preview.valid or not preview.preview:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Шаблон не прошел валидацию",
                "errors": [err.model_dump() for err in preview.errors],
                "warnings": preview.warnings,
            },
        )

    return await _create_template_from_payload(preview.preview, db, context)


@router.get("/{template_id}", response_model=EstimateTemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(
            EstimateTemplate.id == template_id,
            EstimateTemplate.organization_id == context.organization_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template


@router.put("/{template_id}", response_model=EstimateTemplateOut)
async def update_template(
    template_id: int,
    updated_data: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    result = await db.execute(
        select(EstimateTemplate).where(
            EstimateTemplate.id == template_id,
            EstimateTemplate.organization_id == context.organization_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    # Обновление основных полей
    template.name = updated_data.name
    template.description = updated_data.description
    template.use_internal_price = updated_data.use_internal_price

    # Удаление старых услуг
    await db.execute(
        delete(EstimateItem).where(EstimateItem.template_id == template_id)
    )

    # Добавление новых
    for item in updated_data.items:
        db.add(EstimateItem(**item.model_dump(), template_id=template_id))

    await db.commit()

    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == template_id)
    )
    return result.scalar_one()


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(
        select(EstimateTemplate).where(
            EstimateTemplate.id == template_id,
            EstimateTemplate.organization_id == context.organization_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    await db.execute(
        delete(EstimateItem).where(EstimateItem.template_id == template_id)
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="template.deleted",
        entity_type="template",
        entity_id=str(template.id),
        details={
            "template_name": template.name,
        },
        request=request,
    )
    await db.delete(template)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
