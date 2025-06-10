# backend/app/api/templates.py
# Implementation of the templates API endpoints

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

from app.core.database import get_db
from app.models.template import EstimateTemplate
from app.models.item import EstimateItem
from app.schemas.template import EstimateTemplateCreate, EstimateTemplateOut
from app.models.user import User
from app.utils.auth import get_current_user

from typing import List
from app.schemas.pagination import Paginated

router = APIRouter(tags=["templates"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=EstimateTemplateOut)
async def create_template(
    template: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    new_template = EstimateTemplate(
        name=template.name,
        description=template.description,
        user_id=user.id,
        notes=template.notes,
    )
    db.add(new_template)
    await db.flush()

    for item in template.items:
        new_item = EstimateItem(**item.dict(), template_id=new_template.id)
        db.add(new_item)

    await db.commit()

    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == new_template.id)
    )
    return result.scalar_one()


@router.get("/", response_model=Paginated[EstimateTemplateOut])
async def list_templates(
    name: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
):
    query = (
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.user_id == user.id)
    )

    if name:
        query = query.where(EstimateTemplate.name.ilike(f"%{name}%"))

    query = query.order_by(EstimateTemplate.id.desc())
    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{template_id}", response_model=EstimateTemplateOut)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    if template.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")
    return template


@router.put("/{template_id}", response_model=EstimateTemplateOut)
async def update_template(
    template_id: int,
    updated_data: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EstimateTemplate).where(EstimateTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    if template.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")

    # Обновление основных полей
    template.name = updated_data.name
    template.description = updated_data.description
    template.notes = updated_data.notes

    # Удаление старых услуг
    await db.execute(
        delete(EstimateItem).where(EstimateItem.template_id == template_id)
    )

    # Добавление новых
    for item in updated_data.items:
        db.add(EstimateItem(**item.dict(), template_id=template_id))

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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EstimateTemplate).where(EstimateTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    if template.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")

    await db.execute(
        delete(EstimateItem).where(EstimateItem.template_id == template_id)
    )
    await db.delete(template)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
