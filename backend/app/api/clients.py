from typing import List, Optional

from app.core.database import get_db
from app.models.client import Client
from app.models.client_log import ClientChangeLog
from app.models.estimate import Estimate
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.client_log import ClientLogCreate, ClientLogOut
from app.utils.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(tags=["clients"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    new = Client(**client_in.dict(), user_id=user.id)
    db.add(new)
    await db.commit()
    await db.refresh(new)
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


@router.get("/", response_model=List[ClientOut])
async def list_clients(
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Client).where(Client.user_id == user.id)
    if name:
        q = q.where(Client.name.ilike(f"%{name}%"))
    if company:
        q = q.where(Client.company.ilike(f"%{company}%"))
    q = q.order_by(Client.name)
    result = await db.execute(q)
    return result.scalars().all()


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
    for field, val in client_in.dict(exclude_unset=True).items():
        setattr(client, field, val)
    await db.commit()
    await db.refresh(client)
    db.add(
        ClientChangeLog(
            client_id=client.id,
            user_id=user.id,
            action="Обновление",
            description="Данные клиента обновлены",
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
    await db.commit()
    return


@router.get("/{client_id}/logs", response_model=List[ClientLogOut])
async def get_client_logs(
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

    res = await db.execute(
        select(ClientChangeLog)
        .where(ClientChangeLog.client_id == client_id)
        .order_by(ClientChangeLog.timestamp.asc())
    )
    return res.scalars().all()


@router.post("/{client_id}/logs", response_model=ClientLogOut)
async def add_client_log(
    client_id: int,
    log: ClientLogCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == user.id)
    )
    client = res.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    new_log = ClientChangeLog(
        client_id=client_id,
        user_id=user.id,
        action=log.action,
        description=log.description,
    )
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log
