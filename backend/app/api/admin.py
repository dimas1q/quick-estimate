from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client import Client
from app.models.estimate import Estimate, EstimateStatus
from app.models.item import EstimateItem
from app.models.template import EstimateTemplate
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.estimate import EstimateCreate, EstimateOut, EstimateUpdate
from app.schemas.paginated import Paginated
from app.schemas.template import EstimateTemplateCreate, EstimateTemplateOut
from app.schemas.user import (
    AdminActivationUpdate,
    AdminRoleUpdate,
    AdminUserProfileUpdate,
    UserOut,
)
from app.utils.auth import get_current_admin

router = APIRouter(tags=["admin"], dependencies=[Depends(get_current_admin)])


async def _get_user_or_404(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return target_user


async def _get_client_or_404(db: AsyncSession, user_id: int, client_id: int) -> Client:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


async def _ensure_client_owned(db: AsyncSession, user_id: int, client_id: Optional[int]) -> None:
    if client_id is None:
        return
    await _get_client_or_404(db, user_id, client_id)


async def _get_template_or_404(
    db: AsyncSession, user_id: int, template_id: int
) -> EstimateTemplate:
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == template_id, EstimateTemplate.user_id == user_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template


async def _get_estimate_or_404(db: AsyncSession, user_id: int, estimate_id: int) -> Estimate:
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id, Estimate.user_id == user_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    return estimate


@router.get("/users", response_model=Paginated[UserOut])
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_admin: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if search:
        pattern = f"%{search}%"
        filters.append(
            or_(
                User.email.ilike(pattern),
                User.login.ilike(pattern),
                User.name.ilike(pattern),
            )
        )
    if is_admin is not None:
        filters.append(User.is_admin == is_admin)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    total = await db.scalar(select(func.count()).select_from(User).where(*filters))
    result = await db.execute(
        select(User).where(*filters).order_by(User.id.asc()).offset((page - 1) * limit).limit(limit)
    )
    return {"items": result.scalars().all(), "total": total}


@router.get("/users/{user_id}", response_model=UserOut)
async def admin_get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_user_or_404(db, user_id)


@router.put("/users/{user_id}", response_model=UserOut)
async def admin_update_user_profile(
    user_id: int,
    data: AdminUserProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    target_user = await _get_user_or_404(db, user_id)

    normalized_login = data.login.strip()
    normalized_email = data.email.strip().lower()
    normalized_name = data.name.strip() if data.name else None
    normalized_company = data.company.strip() if data.company else None

    if normalized_email != target_user.email:
        existing_by_email = await db.execute(
            select(User).where(User.email == normalized_email, User.id != user_id)
        )
        if existing_by_email.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email уже используется")

    if normalized_login != target_user.login:
        existing_by_login = await db.execute(
            select(User).where(User.login == normalized_login, User.id != user_id)
        )
        if existing_by_login.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Логин уже используется")

    target_user.login = normalized_login
    target_user.email = normalized_email
    target_user.name = normalized_name
    target_user.company = normalized_company

    await db.commit()
    await db.refresh(target_user)
    return target_user


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def admin_update_user_role(
    user_id: int,
    data: AdminRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    target_user = await _get_user_or_404(db, user_id)
    if current_admin.id == user_id and not data.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Нельзя снять роль администратора у самого себя",
        )

    target_user.is_admin = data.is_admin
    await db.commit()
    await db.refresh(target_user)
    return target_user


@router.patch("/users/{user_id}/activation", response_model=UserOut)
async def admin_update_user_activation(
    user_id: int,
    data: AdminActivationUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    target_user = await _get_user_or_404(db, user_id)
    if current_admin.id == user_id and not data.is_active:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать самого себя")

    target_user.is_active = data.is_active
    await db.commit()
    await db.refresh(target_user)
    return target_user


@router.get("/users/{user_id}/clients", response_model=Paginated[ClientOut])
async def admin_list_user_clients(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)

    filters = [Client.user_id == user_id]
    if name:
        filters.append(Client.name.ilike(f"%{name}%"))
    if company:
        filters.append(Client.company.ilike(f"%{company}%"))

    total = await db.scalar(select(func.count()).select_from(Client).where(*filters))
    result = await db.execute(
        select(Client)
        .where(*filters)
        .order_by(Client.name)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return {"items": result.scalars().all(), "total": total}


@router.post("/users/{user_id}/clients", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def admin_create_user_client(
    user_id: int,
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)
    client = Client(**client_in.model_dump(), user_id=user_id)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/users/{user_id}/clients/{client_id}", response_model=ClientOut)
async def admin_update_user_client(
    user_id: int,
    client_id: int,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_db),
):
    client = await _get_client_or_404(db, user_id, client_id)
    for field, value in client_in.model_dump().items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/users/{user_id}/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user_client(
    user_id: int,
    client_id: int,
    db: AsyncSession = Depends(get_db),
):
    client = await _get_client_or_404(db, user_id, client_id)

    estimates_count = await db.scalar(
        select(func.count())
        .select_from(Estimate)
        .where(Estimate.client_id == client_id, Estimate.user_id == user_id)
    )
    if estimates_count and estimates_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Сначала удалите все сметы, связанные с этим клиентом",
        )

    await db.delete(client)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/templates", response_model=Paginated[EstimateTemplateOut])
async def admin_list_user_templates(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)

    filters = [EstimateTemplate.user_id == user_id]
    if name:
        filters.append(EstimateTemplate.name.ilike(f"%{name}%"))

    total = await db.scalar(
        select(func.count()).select_from(EstimateTemplate).where(*filters)
    )
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(*filters)
        .order_by(EstimateTemplate.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return {"items": result.scalars().all(), "total": total}


@router.post(
    "/users/{user_id}/templates",
    response_model=EstimateTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_user_template(
    user_id: int,
    template_in: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)

    template = EstimateTemplate(
        name=template_in.name,
        description=template_in.description,
        use_internal_price=template_in.use_internal_price,
        user_id=user_id,
    )
    db.add(template)
    await db.flush()

    for item in template_in.items:
        db.add(EstimateItem(**item.model_dump(), template_id=template.id))

    await db.commit()
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == template.id)
    )
    return result.scalar_one()


@router.get("/users/{user_id}/templates/{template_id}", response_model=EstimateTemplateOut)
async def admin_get_user_template(
    user_id: int,
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await _get_template_or_404(db, user_id, template_id)


@router.put("/users/{user_id}/templates/{template_id}", response_model=EstimateTemplateOut)
async def admin_update_user_template(
    user_id: int,
    template_id: int,
    template_in: EstimateTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template_or_404(db, user_id, template_id)

    template.name = template_in.name
    template.description = template_in.description
    template.use_internal_price = template_in.use_internal_price

    await db.execute(delete(EstimateItem).where(EstimateItem.template_id == template.id))
    for item in template_in.items:
        db.add(EstimateItem(**item.model_dump(), template_id=template.id))

    await db.commit()
    result = await db.execute(
        select(EstimateTemplate)
        .options(selectinload(EstimateTemplate.items))
        .where(EstimateTemplate.id == template.id)
    )
    return result.scalar_one()


@router.delete("/users/{user_id}/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user_template(
    user_id: int,
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    template = await _get_template_or_404(db, user_id, template_id)

    await db.execute(delete(EstimateItem).where(EstimateItem.template_id == template.id))
    await db.delete(template)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/estimates", response_model=Paginated[EstimateOut])
async def admin_list_user_estimates(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = Query(None),
    status_value: Optional[EstimateStatus] = Query(None, alias="status"),
    client_id: Optional[int] = Query(None, alias="client"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)

    filters = [Estimate.user_id == user_id]
    if name:
        filters.append(Estimate.name.ilike(f"%{name}%"))
    if status_value is not None:
        filters.append(Estimate.status == status_value)
    if client_id is not None:
        filters.append(Estimate.client_id == client_id)
    if date_from:
        try:
            filters.append(Estimate.date >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            filters.append(Estimate.date < datetime.fromisoformat(date_to))
        except ValueError:
            pass

    total = await db.scalar(select(func.count()).select_from(Estimate).where(*filters))
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(*filters)
        .order_by(Estimate.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return {"items": result.scalars().all(), "total": total}


@router.post(
    "/users/{user_id}/estimates",
    response_model=EstimateOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_user_estimate(
    user_id: int,
    estimate_in: EstimateCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_user_or_404(db, user_id)
    await _ensure_client_owned(db, user_id, estimate_in.client_id)

    estimate = Estimate(**estimate_in.model_dump(exclude={"items"}), user_id=user_id)
    db.add(estimate)
    await db.flush()

    for item in estimate_in.items or []:
        db.add(EstimateItem(**item.model_dump(), estimate_id=estimate.id))

    await db.commit()
    return await _get_estimate_or_404(db, user_id, estimate.id)


@router.get("/users/{user_id}/estimates/{estimate_id}", response_model=EstimateOut)
async def admin_get_user_estimate(
    user_id: int,
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await _get_estimate_or_404(db, user_id, estimate_id)


@router.put("/users/{user_id}/estimates/{estimate_id}", response_model=EstimateOut)
async def admin_update_user_estimate(
    user_id: int,
    estimate_id: int,
    estimate_in: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
):
    estimate = await _get_estimate_or_404(db, user_id, estimate_id)
    await _ensure_client_owned(db, user_id, estimate_in.client_id)

    for field, value in estimate_in.model_dump(exclude={"items"}).items():
        setattr(estimate, field, value)

    await db.execute(delete(EstimateItem).where(EstimateItem.estimate_id == estimate.id))
    for item in estimate_in.items or []:
        item_payload = item.model_dump()
        item_payload.pop("id", None)
        db.add(EstimateItem(**item_payload, estimate_id=estimate.id))

    await db.commit()
    return await _get_estimate_or_404(db, user_id, estimate.id)


@router.delete("/users/{user_id}/estimates/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user_estimate(
    user_id: int,
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
):
    estimate = await _get_estimate_or_404(db, user_id, estimate_id)
    await db.delete(estimate)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
