# backend/app/api/versions.py
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client_changelog import ClientChangeLog
from app.models.client import Client
from app.models.estimate import Estimate
from app.models.item import EstimateItem
from app.models.version import EstimateVersion
from app.schemas.estimate import EstimateOut
from app.schemas.version import VersionOut
from app.schemas.paginated import Paginated
from app.utils.auth import get_current_user
from app.utils.workspace import (
    WORKSPACE_PERMISSION_DATA_EDIT,
    WORKSPACE_PERMISSION_DATA_VIEW,
    WorkspaceContext,
    require_workspace_permission,
)

router = APIRouter(
    tags=["versions"],
    dependencies=[Depends(get_current_user)],
)


def _ensure_estimate_not_read_only(est: Estimate):
    if est.read_only:
        raise HTTPException(409, "Смета находится в режиме только чтение")


def _parse_datetime(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    return value


@router.get("/", response_model=Paginated[VersionOut])
async def list_versions(
    estimate_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    # проверяем, что смета принадлежит пользователю
    est = await db.get(Estimate, estimate_id)
    if not est or est.organization_id != context.organization_id:
        raise HTTPException(404, "Смета не найдена или нет доступа")

    count_q = (
        select(func.count())
        .select_from(EstimateVersion)
        .where(EstimateVersion.estimate_id == estimate_id)
    )
    total = await db.scalar(count_q)

    q = await db.execute(
        select(EstimateVersion)
        .where(EstimateVersion.estimate_id == estimate_id)
        .order_by(EstimateVersion.version.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return {"items": q.scalars().all(), "total": total}


@router.get("/{version}", response_model=VersionOut)
async def get_version(
    estimate_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    est = await db.get(Estimate, estimate_id)
    if not est or est.organization_id != context.organization_id:
        raise HTTPException(404, "Смета не найдена или нет доступа")

    q = await db.execute(
        select(EstimateVersion).where(
            EstimateVersion.estimate_id == estimate_id,
            EstimateVersion.version == version,
        )
    )
    v = q.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Версия не найдена")
    return v


@router.post("/{version}/restore", response_model=EstimateOut)
async def restore_version(
    estimate_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    # 1) взять версию
    q = await db.execute(
        select(EstimateVersion).where(
            EstimateVersion.estimate_id == estimate_id,
            EstimateVersion.version == version,
        )
    )
    ver = q.scalar_one_or_none()
    if not ver:
        raise HTTPException(404, "Версия не найдена")

    # 2) загрузить текущую смету и проверить права

    q_est = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )

    est = q_est.scalar_one_or_none()

    if not est or est.organization_id != context.organization_id:
        raise HTTPException(404, "Смета не найдена или нет доступа")
    _ensure_estimate_not_read_only(est)

    data = ver.payload
    restore_fields = {
        "name",
        "responsible",
        "event_place",
        "status",
        "vat_enabled",
        "vat_rate",
        "use_internal_price",
        "client_id",
        "event_datetime",
    }

    new_client_id = data.get("client_id")
    if new_client_id is not None:
        client = await db.get(Client, new_client_id)
        if not client or client.organization_id != context.organization_id:
            raise HTTPException(403, "Нет доступа к клиенту из сохраненной версии")

    for field in restore_fields:
        if field not in data:
            continue
        value = data[field]
        if field == "event_datetime":
            value = _parse_datetime(value)
        setattr(est, field, value)

    # удаляем старые item’ы и вставляем из payload
    await db.execute(
        delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id)
    )
    for item in data.get("items", []):
        item_payload = dict(item)
        item_payload.pop("id", None)
        db.add(EstimateItem(**item_payload, estimate_id=estimate_id))

    # 5) добавим запись в change_log
    from app.models.changelog import EstimateChangeLog

    db.add(
        EstimateChangeLog(
            estimate_id=estimate_id,
            user_id=user.id,
            action="Восстановление",
            description=f"Восстановлена версия #{version}",
        )
    )
    if est.client_id:
        db.add(
            ClientChangeLog(
                client_id=est.client_id,
                user_id=user.id,
                action="Восстановление сметы",
                description=f"Восстановлена версия #{version} для сметы {est.name}",
            )
        )

    await db.commit()

    # 6) вернуть обновлённую смету
    await db.refresh(est)
    return est


@router.delete("/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    estimate_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    # 1) проверка прав
    est = await db.get(Estimate, estimate_id)
    if not est or est.organization_id != context.organization_id:
        raise HTTPException(404, "Смета не найдена или нет доступа")
    _ensure_estimate_not_read_only(est)
    # 2) найти сам снимок
    q = await db.execute(
        select(EstimateVersion).where(
            EstimateVersion.estimate_id == estimate_id,
            EstimateVersion.version == version,
        )
    )
    ver = q.scalar_one_or_none()
    if not ver:
        raise HTTPException(404, "Версия не найдена")
    # 3) удалить
    await db.execute(
        delete(EstimateVersion).where(
            EstimateVersion.estimate_id == estimate_id,
            EstimateVersion.version == version,
        )
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
