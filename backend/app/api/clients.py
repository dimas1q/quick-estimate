## backend/app/api/clients.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client import Client
from app.models.client_changelog import ClientChangeLog
from app.models.estimate import Estimate
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.client_changelog import ClientChangeLogOut
from app.schemas.pagination import Paginated
from app.utils.auth import get_current_user

router = APIRouter(tags=["clients"], dependencies=[Depends(get_current_user)])

FIELD_NAMES_RU = {
    "name": "Изменено имя",
    "company": "Изменена компания",
    "email": "Изменен email",
    "phone": "Изменен телефон",
    "account": "Изменён расчетный счет",
    "corr_account": "Изменён корр. счет",
    "actual_address": "Изменён факт. адрес",
    "legal_address": "Изменён юр. адрес",
    "inn": "Изменён ИНН",
    "kpp": "Изменён КПП",
    "bik": "Изменён БИК",
    "bank": "Изменён банк",
    "notes": "Изменены примечания",
}


@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    new = Client(**client_in.dict(), user_id=user.id)
    db.add(new)
    await db.flush()
    db.add(
        ClientChangeLog(
            client_id=new.id,
            user_id=user.id,
            action="Создание",
            description="Клиент создан",
        )
    )
    await db.commit()
    await db.refresh(new)
    return new


@router.get("/", response_model=Paginated[ClientOut])
async def list_clients(
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = select(Client).where(Client.user_id == user.id)
    if name:
        q = q.where(Client.name.ilike(f"%{name}%"))
    if company:
        q = q.where(Client.company.ilike(f"%{company}%"))
    q = q.order_by(Client.name)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.limit(limit).offset(offset))
    return {
        "items": result.scalars().all(),
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.get("/{client_id}/logs", response_model=Paginated[ClientChangeLogOut])
async def get_client_logs(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    base_q = (
        select(ClientChangeLog)
        .options(selectinload(ClientChangeLog.user))
        .where(ClientChangeLog.client_id == client_id)
    )
    total = await db.scalar(select(func.count()).select_from(base_q.subquery()))

    q = await db.execute(
        base_q.order_by(ClientChangeLog.timestamp.asc()).limit(limit).offset(offset)
    )

    items = [
        ClientChangeLogOut(
            id=log.id,
            action=log.action,
            description=log.description,
            details=log.details,
            timestamp=log.timestamp,
            user_id=log.user_id,
            user_name=log.user.name if log.user else None,
        )
        for log in q.scalars().all()
    ]

    return {"items": items, "meta": {"total": total, "limit": limit, "offset": offset}}


@router.put("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    details = []
    for field, val in client_in.dict(exclude_unset=True).items():
        old_val = getattr(client, field)
        if old_val != val:
            ru = FIELD_NAMES_RU.get(field, field)
            details.append(
                {
                    "label": ru,
                    "old": str(old_val) if old_val is not None else "—",
                    "new": str(val) if val is not None else "—",
                }
            )
        setattr(client, field, val)

    if details:
        db.add(
            ClientChangeLog(
                client_id=client_id,
                user_id=user.id,
                action="Обновление",
                description="Клиент обновлен",
                details=details,
            )
        )

    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    estimates_count = await db.scalar(
        select(func.count())
        .select_from(Estimate)
        .where(Estimate.client_id == client_id)
    )

    if estimates_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Сначала удалите все сметы, связанные с этим клиентом",
        )

    await db.delete(client)
    db.add(
        ClientChangeLog(
            client_id=client_id,
            user_id=user.id,
            action="Удаление",
            description="Клиент удален",
        )
    )
    await db.commit()
    return
