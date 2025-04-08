from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

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

# @router.post("/", response_model=EstimateOut)
# async def create_estimate(estimate: EstimateCreate, db: AsyncSession = Depends(get_db)):
#     items_data = estimate.items or []
#     new_estimate = Estimate(**estimate.dict(exclude={"items"}))
#     db.add(new_estimate)
#     await db.flush()
    
#     for item in items_data:
#         db.add(EstimateItem(**item.dict(), estimate_id=new_estimate.id))
        
#     await db.commit()
#     await db.refresh(new_estimate, options=[selectinload(Estimate.items)])
#     return new_estimate

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
