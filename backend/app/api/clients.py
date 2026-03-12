## backend/app/api/clients.py

from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.client import Client, ClientPipelineStage
from app.models.client_changelog import ClientChangeLog
from app.models.estimate import Estimate, EstimateStatus
from app.models.user import User
from app.schemas.client import (
    ClientCreate,
    ClientOut,
    ClientPipelineItem,
    ClientPipelineOut,
    ClientPipelineSummary,
    ClientPipelineUpdate,
    ClientUpdate,
)
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

PIPELINE_STAGE_LABELS_RU = {
    ClientPipelineStage.LEAD: "Лид",
    ClientPipelineStage.QUOTE: "КП",
    ClientPipelineStage.APPROVED: "Согласовано",
    ClientPipelineStage.PAID: "Оплачено",
}

PIPELINE_FORECAST_WEIGHTS = {
    ClientPipelineStage.LEAD: 0.1,
    ClientPipelineStage.QUOTE: 0.4,
    ClientPipelineStage.APPROVED: 0.75,
    ClientPipelineStage.PAID: 1.0,
}


def prettify_value(val):
    if val in [None, ""]:
        return "—"
    return str(val)


def _estimate_total_with_vat(estimate: Estimate) -> float:
    total_external = sum(
        (item.external_price or 0) * (item.quantity or 0) for item in estimate.items
    )
    vat = total_external * ((estimate.vat_rate or 0) / 100) if estimate.vat_enabled else 0
    return float(total_external + vat)


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
    pipeline_stage: Optional[ClientPipelineStage] = Query(None),
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
    if pipeline_stage:
        filters.append(Client.pipeline_stage == pipeline_stage)

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


@router.get("/pipeline", response_model=ClientPipelineOut)
async def get_clients_pipeline(
    name: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    pipeline_stage: Optional[ClientPipelineStage] = Query(None),
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
    if pipeline_stage:
        filters.append(Client.pipeline_stage == pipeline_stage)

    clients_result = await db.execute(select(Client).where(*filters).order_by(Client.name))
    clients = clients_result.scalars().all()
    if not clients:
        return ClientPipelineOut(
            summary=ClientPipelineSummary(
                lead_count=0,
                quote_count=0,
                approved_count=0,
                paid_count=0,
                total_expected_revenue=0,
                weighted_forecast=0,
            ),
            items=[],
        )

    client_ids = [client.id for client in clients]
    estimates_result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items))
        .where(
            Estimate.user_id == user.id,
            Estimate.client_id.in_(client_ids),
        )
        .order_by(Estimate.date.desc())
    )
    estimates = estimates_result.scalars().all()

    estimates_by_client: dict[int, list[Estimate]] = defaultdict(list)
    for estimate in estimates:
        if estimate.client_id is not None:
            estimates_by_client[int(estimate.client_id)].append(estimate)

    summary_counts = {
        ClientPipelineStage.LEAD: 0,
        ClientPipelineStage.QUOTE: 0,
        ClientPipelineStage.APPROVED: 0,
        ClientPipelineStage.PAID: 0,
    }
    total_expected_revenue = 0.0
    weighted_forecast = 0.0
    items: list[ClientPipelineItem] = []

    for client in clients:
        stage = client.pipeline_stage or ClientPipelineStage.LEAD
        summary_counts[stage] += 1

        client_estimates = estimates_by_client.get(client.id, [])
        last_estimate = client_estimates[0] if client_estimates else None
        paid_revenue = 0.0
        open_revenue = 0.0
        for estimate in client_estimates:
            estimate_total = _estimate_total_with_vat(estimate)
            if estimate.status == EstimateStatus.PAID:
                paid_revenue += estimate_total
            elif estimate.status in {
                EstimateStatus.DRAFT,
                EstimateStatus.SENT,
                EstimateStatus.APPROVED,
            }:
                open_revenue += estimate_total

        expected_revenue = (
            float(client.pipeline_expected_revenue)
            if (client.pipeline_expected_revenue or 0) > 0
            else open_revenue
        )
        forecast_amount = expected_revenue * PIPELINE_FORECAST_WEIGHTS[stage]
        total_expected_revenue += expected_revenue
        weighted_forecast += forecast_amount

        items.append(
            ClientPipelineItem(
                id=client.id,
                name=client.name,
                company=client.company,
                pipeline_stage=stage,
                pipeline_expected_revenue=expected_revenue,
                forecast_amount=forecast_amount,
                estimates_count=len(client_estimates),
                last_estimate_date=last_estimate.date if last_estimate else None,
                last_estimate_status=last_estimate.status if last_estimate else None,
                open_revenue=open_revenue,
                paid_revenue=paid_revenue,
            )
        )

    stage_order = {
        ClientPipelineStage.LEAD: 0,
        ClientPipelineStage.QUOTE: 1,
        ClientPipelineStage.APPROVED: 2,
        ClientPipelineStage.PAID: 3,
    }
    items.sort(
        key=lambda item: (
            stage_order.get(item.pipeline_stage, 99),
            -item.forecast_amount,
            item.name.lower(),
        )
    )

    return ClientPipelineOut(
        summary=ClientPipelineSummary(
            lead_count=summary_counts[ClientPipelineStage.LEAD],
            quote_count=summary_counts[ClientPipelineStage.QUOTE],
            approved_count=summary_counts[ClientPipelineStage.APPROVED],
            paid_count=summary_counts[ClientPipelineStage.PAID],
            total_expected_revenue=total_expected_revenue,
            weighted_forecast=weighted_forecast,
        ),
        items=items,
    )


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


@router.patch("/{client_id}/pipeline", response_model=ClientOut)
async def update_client_pipeline(
    client_id: int,
    payload: ClientPipelineUpdate,
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
    update_data = payload.dict(exclude_unset=True)

    if "pipeline_stage" in update_data:
        new_stage = update_data["pipeline_stage"]
        if client.pipeline_stage != new_stage:
            details.append(
                {
                    "label": "Этап воронки",
                    "old": PIPELINE_STAGE_LABELS_RU.get(client.pipeline_stage, "—"),
                    "new": PIPELINE_STAGE_LABELS_RU.get(new_stage, "—"),
                }
            )
            client.pipeline_stage = new_stage

    if "pipeline_expected_revenue" in update_data:
        new_revenue = float(update_data["pipeline_expected_revenue"] or 0)
        old_revenue = float(client.pipeline_expected_revenue or 0)
        if abs(old_revenue - new_revenue) >= 0.01:
            details.append(
                {
                    "label": "Ожидаемая выручка",
                    "old": f"{old_revenue:.2f} ₽",
                    "new": f"{new_revenue:.2f} ₽",
                }
            )
            client.pipeline_expected_revenue = new_revenue

    if details:
        db.add(
            ClientChangeLog(
                client_id=client_id,
                user_id=user.id,
                action="Pipeline",
                description="Обновлен этап продаж клиента",
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
