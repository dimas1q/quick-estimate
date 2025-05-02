# backend/app/api/estimates.py
# Implementation of the estimates API endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, or_, func

from app.models.estimate import Estimate
from app.models.item import EstimateItem
from app.schemas.estimate import EstimateCreate, EstimateOut
from app.schemas.changelog import ChangeLogOut
from app.core.database import get_db
from app.models.changelog import EstimateChangeLog
from app.utils.auth import get_current_user
from app.utils.pdf import render_pdf
from app.utils.excel import generate_excel
from app.models.user import User
from app.models.client import Client

from typing import Optional
from typing import List
from urllib.parse import quote
import re

router = APIRouter(
    tags=["estimates"], dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=EstimateOut)
async def create_estimate(
    estimate: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
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
            action="Создание",
            description=f"Смета создана",
        )
    )

    await db.commit()

    # greenlet
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == new_estimate.id)
    )
    new_estimate = result.scalar_one()
    return new_estimate


@router.get("/", response_model=List[EstimateOut])
async def list_estimates(
    name: str = Query(None),
    client: Optional[int] = Query(None),  # Change type to Optional[int]
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    from datetime import datetime
    query = (
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.user_id == user.id)
    )

    if name:
        query = query.where(Estimate.name.ilike(f"%{name}%"))
    if client:
        query = query.where(Estimate.client_id == client)  # Adjust to filter by client ID
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

    result = await db.execute(query.order_by(Estimate.id.desc()))
    return result.scalars().all()

@router.get("/{estimate_id}", response_model=EstimateOut)
async def get_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
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

    return estimate


@router.get("/{estimate_id}/logs", response_model=List[ChangeLogOut])
async def get_logs(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Load the estimate and check access
    result = await db.execute(
        select(Estimate).where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    # Fetch and return logs
    result = await db.execute(
        select(EstimateChangeLog)
        .where(EstimateChangeLog.estimate_id == estimate_id)
        .order_by(EstimateChangeLog.timestamp.asc())
    )

    return result.scalars().all()

@router.get("/{estimate_id}/export/pdf")
async def export_estimate_pdf(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.user_id != user.id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")

    total = sum(item.unit_price * item.quantity for item in estimate.items)

    pdf_bytes = render_pdf("estimate_pdf.html", {"estimate": estimate, "total": total})
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=estimate_{estimate.id}.pdf"}
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
    ascii_filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    utf8_filename = quote(filename)

    excel_file = generate_excel(estimate)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_filename}; filename*=UTF-8''{utf8_filename}"
        }
    )


@router.put("/{estimate_id}", response_model=EstimateOut)
async def update_estimate(
    estimate_id: int,
    updated_data: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()

    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    
    if estimate.user_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    # обновим основные поля
    for field, value in updated_data.dict(exclude={"items"}).items():
        setattr(estimate, field, value)

    # удалим старые строки и добавим новые
    await db.execute(
        delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id)
    )
    for item in updated_data.items:
        db.add(EstimateItem(**item.dict(), estimate_id=estimate_id))

    db.add(
        EstimateChangeLog(
            estimate_id=estimate_id,
            action="Обновление",
            description="Смета обновлена",
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
    user: User = Depends(get_current_user)
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
