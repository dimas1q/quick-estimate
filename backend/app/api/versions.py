# backend/app/api/versions.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client_changelog import ClientChangeLog
from app.models.estimate import Estimate
from app.models.item import EstimateItem
from app.models.version import EstimateVersion
from app.schemas.estimate import EstimateOut
from app.schemas.version import VersionOut
from app.schemas.pagination import Paginated
from app.utils.auth import get_current_user

router = APIRouter(
    tags=["versions"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=Paginated[VersionOut])
async def list_versions(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # проверяем, что смета принадлежит пользователю
    est = await db.get(Estimate, estimate_id)
    if not est or est.user_id != user.id:
        raise HTTPException(404, "Смета не найдена или нет доступа")

    base_q = select(EstimateVersion).where(EstimateVersion.estimate_id == estimate_id)
    total = await db.scalar(select(func.count()).select_from(base_q.subquery()))

    q = await db.execute(
        base_q.order_by(EstimateVersion.version.asc()).limit(limit).offset(offset)
    )
    return {
        "items": q.scalars().all(),
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/{version}", response_model=VersionOut)
async def get_version(
    estimate_id: int,
    version: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    est = await db.get(Estimate, estimate_id)
    if not est or est.user_id != user.id:
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
    user=Depends(get_current_user),
):
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

    if not est or est.user_id != user.id:
        raise HTTPException(404, "Смета не найдена или нет доступа")

    data = ver.payload
    # обновляем поля
    for f, v in data.items():
        if f in {"name", "notes", "responsible", "vat_enabled", "client_id", "status"}:
            setattr(est, f, v)
    # удаляем старые item’ы и вставляем из payload
    await db.execute(
        delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id)
    )
    for it in data["items"]:
        db.add(EstimateItem(**it, estimate_id=estimate_id))

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
    user=Depends(get_current_user),
):
    # 1) проверка прав
    est = await db.get(Estimate, estimate_id)
    if not est or est.user_id != user.id:
        raise HTTPException(404, "Смета не найдена или нет доступа")
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
