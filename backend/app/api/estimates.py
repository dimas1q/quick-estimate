from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete

from app.models.estimate import Estimate
from app.models.item import EstimateItem
from app.schemas.estimate import EstimateCreate, EstimateOut
from app.core.database import SessionLocal

from typing import List

router = APIRouter()

# Получаем сессию к БД через Depends
async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/", response_model=EstimateOut)
async def create_estimate(estimate: EstimateCreate, db: AsyncSession = Depends(get_db)):
    items_data = estimate.items or []
    new_estimate = Estimate(**estimate.dict(exclude={"items"}))
    db.add(new_estimate)
    await db.flush()  # получаем ID

    for item in items_data:
        db.add(EstimateItem(**item.dict(), estimate_id=new_estimate.id))

    await db.commit()

    # загружаем estimate с items без ошибок greenlet
    result = await db.execute(
        select(Estimate).options(selectinload(Estimate.items)).where(Estimate.id == new_estimate.id)
    )
    new_estimate = result.scalar_one()
    return new_estimate

@router.get("/", response_model=List[EstimateOut])
async def list_estimates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Estimate).options(selectinload(Estimate.items)))
    return result.scalars().all()


@router.get("/{estimate_id}", response_model=EstimateOut)
async def get_estimate(estimate_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    return estimate

@router.put("/{estimate_id}", response_model=EstimateOut)
async def update_estimate(
    estimate_id: int, updated_data: EstimateCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    # обновим основные поля
    for field, value in updated_data.dict(exclude={"items"}).items():
        setattr(estimate, field, value)

    # удалим старые строки и добавим новые
    await db.execute(
        delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id)
    )
    for item in updated_data.items:
        db.add(EstimateItem(**item.dict(), estimate_id=estimate_id))

    await db.commit()

    # вернём обновлённую
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items))
        .where(Estimate.id == estimate_id)
    )
    return result.scalar_one()


@router.delete("/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_estimate(estimate_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    await db.delete(estimate)
    await db.commit()
    return JSONResponse(status_code=204, content=None)
