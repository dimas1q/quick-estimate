# backend/app/api/estimates.py
# Implementation of the estimates API endpoints
import re
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.changelog import EstimateChangeLog
from app.models.client_changelog import ClientChangeLog
from app.models.estimate import Estimate
from app.models.estimate_favorite import EstimateFavorite
from app.models.item import EstimateItem
from app.models.user import User
from app.models.version import EstimateVersion
from app.schemas.changelog import ChangeLogOut
from app.schemas.pagination import Paginated
from app.schemas.estimate import EstimateCreate, EstimateOut, EstimateUpdate
from app.utils.auth import get_current_user
from app.utils.excel import generate_excel
from app.utils.pdf import render_pdf

from datetime import datetime
from datetime import timezone

router = APIRouter(tags=["estimates"], dependencies=[Depends(get_current_user)])

FIELD_NAMES_RU = {
    "name": "Изменено название",
    "client_id": "Изменен клиент",
    "responsible": "Изменен ответственный",
    "status": "Изменен статус",
    "event_datetime": "Изменено дата и время проведения мероприятия",
    "event_place": "Изменено место проведения мероприятия",
    "notes": "Изменены заметки",
}
ITEM_FIELD_NAMES_RU = {
    "name": "Изменено название услуги",
    "description": "Изменено описание услуги",
    "quantity": "Изменено количество услуги",
    "unit": "Изменена единица измерения услуги",
    "internal_price": "Изменена внутренняя цена услуги",
    "external_price": "Изменена внешняя цена услуги",
}

STATUS_LABELS_RU = {
    "draft": "Черновик",
    "sent": "Отправлена",
    "approved": "Согласована",
    "paid": "Оплачена",
    "cancelled": "Отменена",
}


@router.post("/", response_model=EstimateOut)
async def create_estimate(
    estimate: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items_data = estimate.items or []
    new_estimate = Estimate(**estimate.dict(exclude={"items"}), user_id=user.id)
    db.add(new_estimate)
    await db.flush()

    for item in items_data:
        db.add(EstimateItem(**item.dict(), estimate_id=new_estimate.id))

    db.add(
        EstimateChangeLog(
            estimate_id=new_estimate.id,
            user_id=user.id,
            action="Создание",
            description="Смета создана",
        )
    )
    db.add(
        ClientChangeLog(
            client_id=new_estimate.client_id,
            user_id=user.id,
            action="Создание сметы",
            description=f"Создана смета: {new_estimate.name}",
        )
    )

    await db.commit()

    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == new_estimate.id)
    )

    return result.scalar_one()


@router.get("/", response_model=Paginated[EstimateOut])
async def list_estimates(
    name: str = Query(None),
    client: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    favorite: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
):

    query = (
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.user_id == user.id)
    )

    if name:
        query = query.where(Estimate.name.ilike(f"%{name}%"))
    if client:
        query = query.where(Estimate.client_id == client)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(Estimate.date >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.where(Estimate.date < dt_to)
        except ValueError:
            pass
    if favorite:
        query = query.join(EstimateFavorite).where(EstimateFavorite.user_id == user.id)

    count_query = select(func.count()).select_from(Estimate)
    if favorite:
        count_query = count_query.join(EstimateFavorite).where(EstimateFavorite.user_id == user.id)
    count_query = count_query.where(Estimate.user_id == user.id)
    if name:
        count_query = count_query.where(Estimate.name.ilike(f"%{name}%"))
    if client:
        count_query = count_query.where(Estimate.client_id == client)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            count_query = count_query.where(Estimate.date >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            count_query = count_query.where(Estimate.date < dt_to)
        except ValueError:
            pass

    total = await db.scalar(count_query)

    result = await db.execute(
        query.order_by(Estimate.id.desc()).offset(offset).limit(limit)
    )

    estimates = result.scalars().all()

    # Получаем id всех избранных смет для текущего пользователя
    fav_result = await db.execute(
        select(EstimateFavorite.estimate_id).where(EstimateFavorite.user_id == user.id)
    )
    favorite_ids = set(fav_result.scalars().all())

    for estimate in estimates:
        estimate.is_favorite = estimate.id in favorite_ids

    return {
        "items": estimates,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{estimate_id}", response_model=EstimateOut)
async def get_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    fav = await db.execute(
        select(EstimateFavorite).where(
            EstimateFavorite.user_id == user.id,
            EstimateFavorite.estimate_id == estimate_id,
        )
    )
    estimate.is_favorite = fav.scalar_one_or_none() is not None
    return estimate


@router.get("/{estimate_id}/logs", response_model=Paginated[ChangeLogOut])
async def get_logs(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(15, ge=1),
    offset: int = Query(0, ge=0),
):
    # Load the estimate and check access
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    # Fetch and return logs
    count_query = select(func.count()).select_from(EstimateChangeLog).where(
        EstimateChangeLog.estimate_id == estimate_id
    )
    total = await db.scalar(count_query)

    result = await db.execute(
        select(EstimateChangeLog)
        .options(selectinload(EstimateChangeLog.user))
        .where(EstimateChangeLog.estimate_id == estimate_id)
        .order_by(EstimateChangeLog.timestamp.asc())
        .offset(offset)
        .limit(limit)
    )

    logs = [
        ChangeLogOut(
            id=log.id,
            action=log.action,
            description=log.description,
            details=log.details,
            timestamp=log.timestamp,
            user_id=log.user_id,
            user_name=log.user.name or log.user.login if log.user else None,
        )
        for log in result.scalars().all()
    ]

    return {"items": logs, "total": total, "limit": limit, "offset": offset}


@router.get("/{estimate_id}/export/pdf")
async def export_estimate_pdf(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.user_id != user.id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")

    # --- Новые суммы ---
    total_internal = sum(
        (item.internal_price or 0) * (item.quantity or 0) for item in estimate.items
    )
    total_external = sum(
        (item.external_price or 0) * (item.quantity or 0) for item in estimate.items
    )
    total_diff = total_external - total_internal
    vat = total_external * (estimate.vat_rate / 100) if estimate.vat_enabled else 0
    total_with_vat = total_external + vat

    pdf_bytes = render_pdf(
        "estimate_pdf.html",
        {
            "estimate": estimate,
            "total_internal": total_internal,
            "total_external": total_external,
            "total_diff": total_diff,
            "vat": vat,
            "total_with_vat": total_with_vat,
        },
    )
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=estimate_{estimate.id}.pdf"
        },
    )


@router.get("/{estimate_id}/export/excel")
async def export_estimate_excel(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()

    if not estimate or estimate.user_id != user.id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")

    filename = f"{estimate.name}.xlsx"
    ascii_filename = re.sub(r"[^\x00-\x7F]+", "_", filename)
    utf8_filename = quote(filename)

    excel_file = generate_excel(estimate)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_filename}; filename*=UTF-8''{utf8_filename}"
        },
    )


@router.put("/{estimate_id}", response_model=EstimateOut)
async def update_estimate(
    estimate_id: int,
    updated_data: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()

    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )

    old_estimate = result.scalar_one_or_none()

    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    old_out = EstimateOut.from_orm(old_estimate)
    old_payload = jsonable_encoder(old_out)

    max_ver = (
        await db.scalar(
            select(func.max(EstimateVersion.version)).where(
                EstimateVersion.estimate_id == estimate_id
            )
        )
        or 0
    )
    next_ver = max_ver + 1

    db.add(
        EstimateVersion(
            estimate_id=estimate_id,
            version=next_ver,
            user_id=user.id,
            payload=old_payload,
        )
    )

    # ==== Новый блок сравнения ====
    details = []

    # Логика для НДС
    if estimate.vat_enabled != updated_data.vat_enabled:
        details.append("Включен НДС" if updated_data.vat_enabled else "Выключен НДС")
    estimate.vat_enabled = updated_data.vat_enabled

    if estimate.vat_rate != updated_data.vat_rate:
        details.append(
            {
                "label": "Изменена ставка НДС",
                "old": f"{estimate.vat_rate}%",
                "new": f"{updated_data.vat_rate}%",
            }
        )
    estimate.vat_rate = updated_data.vat_rate

    # Простые поля (кроме items, vat_enabled, vat_rate)
    for field, value in updated_data.dict(
        exclude={"items", "vat_enabled", "vat_rate"}
    ).items():
        old_val = getattr(estimate, field)
        if field == "status":
            old_val = old_val.value if hasattr(old_val, "value") else str(old_val)
            new_val = value.value if hasattr(value, "value") else str(value)
            if old_val != new_val:
                details.append(
                    {
                        "label": FIELD_NAMES_RU.get(field, field),
                        "old": STATUS_LABELS_RU.get(old_val, old_val),
                        "new": STATUS_LABELS_RU.get(new_val, new_val),
                    }
                )
        else:
            ru = FIELD_NAMES_RU.get(field)
            if getattr(estimate, field) != value and ru:
                ru = FIELD_NAMES_RU.get(field)
                if ru:
                    details.append(
                        {
                            "label": ru,
                            "old": str(getattr(estimate, field)),
                            "new": str(value),
                        }
                    )

            setattr(estimate, field, value)

    old_items = {item.id: item for item in old_estimate.items if item.id is not None}
    new_items = {
        item.id: item
        for item in updated_data.items
        if getattr(item, "id", None) is not None
    }

    # Добавленные услуги (новые, которых не было раньше)
    for item in updated_data.items:
        if item.id is None or item.id not in old_items:
            details.append(f"Добавлена услуга ({item.name})")

    # Удалённые услуги (были раньше, но пропали)
    for item_id, item in old_items.items():
        if item_id not in [i.id for i in updated_data.items if i.id is not None]:
            details.append(f"Удалена услуга ({item.name})")

    # Изменения в услугах
    for item_id, old_item in old_items.items():
        new_item = new_items.get(item_id)
        if new_item:
            for f in ITEM_FIELD_NAMES_RU:
                if getattr(old_item, f, None) != getattr(new_item, f, None):
                    ru = ITEM_FIELD_NAMES_RU[f]
                    details.append(
                        {
                            "label": f"{ru} ({new_item.name})",
                            "old": str(getattr(old_item, f, "")),
                            "new": str(getattr(new_item, f, "")),
                        }
                    )

    # Обновление услуг в БД
    await db.execute(
        delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id)
    )
    for item in updated_data.items:
        db.add(EstimateItem(**item.dict(), estimate_id=estimate_id))

    now = datetime.now(timezone.utc)

    db.add(
        EstimateChangeLog(
            estimate_id=estimate_id,
            user_id=user.id,
            action="Обновление",
            description="Смета обновлена",
            details=details if details else None,
            timestamp=now,
        )
    )

    db.add(
        ClientChangeLog(
            client_id=estimate.client_id,
            user_id=user.id,
            action="Изменение сметы",
            description=f"Обновлена смета: {estimate.name}",
        )
    )

    await db.commit()

    # вернём обновлённую
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    return result.scalar_one()


@router.delete("/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()

    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    await db.delete(estimate)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{estimate_id}/favorite/", status_code=204)
async def add_favorite(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Проверяем, что смета существует и принадлежит этому пользователю
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.user_id != user.id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")

    # Проверяем, есть ли уже избранное
    res = await db.execute(
        select(EstimateFavorite).where(
            EstimateFavorite.user_id == user.id,
            EstimateFavorite.estimate_id == estimate_id,
        )
    )
    fav = res.scalar_one_or_none()
    if not fav:
        db.add(EstimateFavorite(user_id=user.id, estimate_id=estimate_id))
        await db.commit()
    return Response(status_code=204)


@router.delete("/{estimate_id}/favorite/", status_code=204)
async def remove_favorite(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(EstimateFavorite).where(
            EstimateFavorite.user_id == user.id,
            EstimateFavorite.estimate_id == estimate_id,
        )
    )
    fav = res.scalar_one_or_none()
    if fav:
        await db.delete(fav)
        await db.commit()
    return Response(status_code=204)
