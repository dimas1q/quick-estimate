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
from app.schemas.paginated import Paginated
from app.schemas.client_changelog import ClientChangeLogOut
from app.utils.auth import get_current_user

router = APIRouter(tags=["clients"], dependencies=[Depends(get_current_user)])

FIELD_ACTIONS_CLIENT_RU = {
    "name": {
        "add": "Добавлено имя",
        "del": "Удалено имя",
        "edit": "Изменено имя",
    },
    "company": {
        "add": "Добавлена компания",
        "del": "Удалена компания",
        "edit": "Изменена компания",
    },
    "email": {"add": "Добавлен email", "del": "Удален email", "edit": "Изменен email"},
    "phone": {
        "add": "Добавлен телефон",
        "del": "Удален телефон",
        "edit": "Изменен телефон",
    },
    "legal_address": {
        "add": "Добавлен юр. адрес",
        "del": "Удален юр. адрес",
        "edit": "Изменен юр. адрес",
    },
    "actual_address": {
        "add": "Добавлен факт. адрес",
        "del": "Удален факт. адрес",
        "edit": "Изменен факт. адрес",
    },
    "inn": {"add": "Добавлен ИНН", "del": "Удален ИНН", "edit": "Изменен ИНН"},
    "kpp": {"add": "Добавлен КПП", "del": "Удален КПП", "edit": "Изменен КПП"},
    "bik": {"add": "Добавлен БИК", "del": "Удален БИК", "edit": "Изменен БИК"},
    "account": {
        "add": "Добавлен расчетный счет",
        "del": "Удален расчетный счет",
        "edit": "Изменен расчетный счет",
    },
    "bank": {"add": "Добавлен банк", "del": "Удален банк", "edit": "Изменен банк"},
    "corr_account": {
        "add": "Добавлен корр. счет",
        "del": "Удален корр. счет",
        "edit": "Изменен корр. счет",
    },
    "notes": {
        "add": "Добавлены примечания",
        "del": "Удалены примечания",
        "edit": "Изменены примечания",
    },
}


def prettify_value(val):
    if val in [None, ""]:
        return "—"
    return str(val)


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
    email: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = [Client.user_id == user.id]
    if name:
        filters.append(Client.name.ilike(f"%{name}%"))
    if company:
        filters.append(Client.company.ilike(f"%{company}%"))
    if email:
        filters.append(Client.email.ilike(f"%{email}%"))

    count_q = select(func.count()).select_from(Client).where(*filters)
    total = await db.scalar(count_q)

    q = (
        select(Client)
        .where(*filters)
        .order_by(Client.name)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(q)
    return {"items": result.scalars().all(), "total": total}


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
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    count_q = (
        select(func.count())
        .select_from(ClientChangeLog)
        .where(ClientChangeLog.client_id == client_id)
    )
    total = await db.scalar(count_q)

    q = await db.execute(
        select(ClientChangeLog)
        .options(selectinload(ClientChangeLog.user))
        .where(ClientChangeLog.client_id == client_id)
        .order_by(ClientChangeLog.timestamp.asc())
        .offset((page - 1) * limit)
        .limit(limit)
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
    return {"items": items, "total": total}


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
        actions = FIELD_ACTIONS_CLIENT_RU.get(field)
        if actions:
            # Добавление
            if not old_val and val:
                details.append(
                    {"label": actions["add"], "old": None, "new": prettify_value(val)}
                )
            # Удаление
            elif old_val and not val:
                details.append(
                    {
                        "label": actions["del"],
                        "old": prettify_value(old_val),
                        "new": None,
                    }
                )
            # Изменение
            elif old_val != val:
                details.append(
                    {
                        "label": actions["edit"],
                        "old": prettify_value(old_val),
                        "new": prettify_value(val),
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
