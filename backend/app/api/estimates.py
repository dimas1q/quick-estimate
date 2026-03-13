# backend/app/api/estimates.py
# Implementation of the estimates API endpoints
import logging
import re
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.changelog import EstimateChangeLog
from app.models.client_changelog import ClientChangeLog
from app.models.estimate import Estimate, EstimateStatus
from app.models.estimate_approval import EstimateApprovalStep, EstimateApprovalWorkflow
from app.models.estimate_favorite import EstimateFavorite
from app.models.item import EstimateItem
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.models.client import Client
from app.models.version import EstimateVersion
from app.schemas.approval import ApprovalWorkflowOut, ApprovalWorkflowUpsertIn
from app.schemas.changelog import ChangeLogOut
from app.schemas.estimate import (
    EstimateAutosave,
    EstimateCreate,
    EstimateProfitGuardCheckIn,
    EstimateProfitGuardCheckOut,
    EstimateOut,
    EstimateReadOnlyUpdate,
    EstimateSendEmail,
    EstimateUpdate,
    ProfitGuardRisk,
)
from app.utils.auth import get_current_user
from app.utils.email import EmailAttachment, send_email
from app.utils.excel import generate_excel
from app.utils.pdf import render_pdf
from app.utils.workspace import (
    WORKSPACE_PERMISSION_APPROVAL_MANAGE,
    WORKSPACE_PERMISSION_DATA_EDIT,
    WORKSPACE_PERMISSION_DATA_VIEW,
    WorkspaceContext,
    require_workspace_permission,
)
from app.services.approval_workflow import (
    STEP_STATUS_PENDING,
    WORKFLOW_STATUS_DRAFT,
    WORKFLOW_STATUS_IN_REVIEW,
    to_workflow_out,
)
from app.services.audit_ledger import append_audit_ledger_entry
from app.schemas.paginated import Paginated

from datetime import datetime
from datetime import timezone

logger = logging.getLogger(__name__)

router = APIRouter(tags=["estimates"], dependencies=[Depends(get_current_user)])

FIELD_ACTIONS_RU = {
    "name": {"edit": "Изменено название"},
    "client_id": {
        "add": "Добавлен клиент",
        "del": "Удален клиент",
        "edit": "Изменен клиент",
    },
    "responsible": {"edit": "Изменен ответственный"},
    "status": {"edit": "Изменен статус"},
    "event_datetime": {
        "add": "Добавлена дата и время проведения мероприятия",
        "del": "Удалена дата и время проведения мероприятия",
        "edit": "Изменена дата и время проведения мероприятия",
    },
    "event_place": {
        "add": "Добавлено место проведения мероприятия",
        "del": "Удалено место проведения мероприятия",
        "edit": "Изменено место проведения мероприятия",
    },
    "notes": {
        "add": "Добавлены примечания",
        "del": "Удалены примечания",
        "edit": "Изменены примечания",
    },
    "service": {
        "add": "Добавлена услуга",
        "del": "Удалена услуга",
    },
    # Услуги
    "item_name": {"edit": "Изменено название услуги"},
    "item_description": {"edit": "Изменено описание услуги"},
    "item_quantity": {"edit": "Изменено количество услуги"},
    "item_unit": {"edit": "Изменена единица измерения услуги"},
    "item_internal_price": {"edit": "Изменена внутренняя цена услуги"},
    "item_external_price": {"edit": "Изменена внешняя цена услуги"},
}

STATUS_LABELS_RU = {
    "draft": "Черновик",
    "sent": "Отправлена",
    "approved": "Согласована",
    "paid": "Оплачена",
    "cancelled": "Отменена",
}


def _round_currency(value: float) -> float:
    return round(float(value or 0.0), 2)


def _round_percent(value: float) -> float:
    return round(float(value or 0.0), 2)


def _build_profit_guard_result(
    payload: EstimateProfitGuardCheckIn,
    *,
    enabled: bool,
    threshold_percent: float,
) -> EstimateProfitGuardCheckOut:
    threshold = max(0.0, float(threshold_percent))
    if not enabled:
        return EstimateProfitGuardCheckOut(
            enabled=False,
            threshold_percent=threshold,
            has_risk=False,
            risk_count=0,
            message="Smart Profit Guard отключен",
            total_internal=0,
            total_external=0,
            total_margin_amount=0,
            overall_margin_percent=0,
            risks=[],
        )

    if not payload.use_internal_price:
        return EstimateProfitGuardCheckOut(
            enabled=True,
            threshold_percent=threshold,
            has_risk=False,
            risk_count=0,
            message="Внутренняя цена отключена, расчет маржи недоступен",
            total_internal=0,
            total_external=0,
            total_margin_amount=0,
            overall_margin_percent=0,
            risks=[],
        )

    total_internal = 0.0
    total_external = 0.0
    risks: List[ProfitGuardRisk] = []

    for index, item in enumerate(payload.items):
        quantity = float(item.quantity or 0)
        internal_price = float(item.internal_price or 0)
        external_price = float(item.external_price or 0)
        internal_total = quantity * internal_price
        external_total = quantity * external_price
        margin_amount = external_total - internal_total

        total_internal += internal_total
        total_external += external_total

        if external_total <= 0:
            continue

        margin_percent = (margin_amount / external_total) * 100
        if margin_percent < threshold:
            risks.append(
                ProfitGuardRisk(
                    index=index,
                    name=(item.name or f"Позиция №{index + 1}").strip(),
                    category=(item.category or "").strip(),
                    margin_percent=_round_percent(margin_percent),
                    margin_amount=_round_currency(margin_amount),
                    internal_total=_round_currency(internal_total),
                    external_total=_round_currency(external_total),
                )
            )

    total_margin_amount = total_external - total_internal
    overall_margin_percent = (
        (total_margin_amount / total_external) * 100 if total_external > 0 else 0.0
    )

    has_risk = len(risks) > 0
    message = (
        f"Найдено {len(risks)} риск-позиций с маржой ниже {threshold:.2f}%"
        if has_risk
        else "Риск-позиций не найдено"
    )
    return EstimateProfitGuardCheckOut(
        enabled=True,
        threshold_percent=_round_percent(threshold),
        has_risk=has_risk,
        risk_count=len(risks),
        message=message,
        total_internal=_round_currency(total_internal),
        total_external=_round_currency(total_external),
        total_margin_amount=_round_currency(total_margin_amount),
        overall_margin_percent=_round_percent(overall_margin_percent),
        risks=sorted(risks, key=lambda risk: risk.margin_percent),
    )


def prettify_value(value):
    if value in [None, ""]:
        return "—"
    return str(value)


def prettify_number(val):
    if val in [None, ""]:
        return "—"
    try:
        v = float(val)
        if v.is_integer():
            return str(int(v))
        else:
            return str(v)
    except Exception:
        return str(val)


async def ensure_client_in_workspace(
    db: AsyncSession,
    client_id: Optional[int],
    organization_id: int,
):
    if client_id is None:
        return None

    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if client.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому клиенту")
    return client


async def ensure_client_belongs_to_user(
    db: AsyncSession,
    client_id: Optional[int],
    user_id: int,
):
    """
    Backward-compatible helper kept for legacy tests and direct imports.
    New runtime access control uses workspace-scoped ensure_client_in_workspace().
    """
    if client_id is None:
        return None

    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if client.user_id != user_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому клиенту")
    return client


def ensure_estimate_not_read_only(estimate: Estimate):
    if estimate.read_only:
        raise HTTPException(
            status_code=409,
            detail="Смета находится в режиме только чтение",
        )


async def ensure_estimate_not_in_active_approval(db: AsyncSession, estimate_id: int):
    workflow_status = await db.scalar(
        select(EstimateApprovalWorkflow.status).where(
            EstimateApprovalWorkflow.estimate_id == estimate_id
        )
    )
    if workflow_status == WORKFLOW_STATUS_IN_REVIEW:
        raise HTTPException(
            status_code=409,
            detail="Смета находится в процессе согласования и недоступна для редактирования",
        )


@router.post("/profit-guard/check", response_model=EstimateProfitGuardCheckOut)
async def check_profit_guard(
    payload: EstimateProfitGuardCheckIn,
    _context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    return _build_profit_guard_result(
        payload,
        enabled=bool(getattr(settings, "PROFIT_GUARD_ENABLED", True)),
        threshold_percent=float(
            getattr(settings, "PROFIT_GUARD_MIN_MARGIN_PERCENT", 15.0)
        ),
    )


def ensure_financial_documents_allowed(estimate: Estimate):
    allowed_statuses = {EstimateStatus.APPROVED, EstimateStatus.PAID}
    if estimate.status not in allowed_statuses:
        raise HTTPException(
            status_code=409,
            detail="Счет и акт доступны только для согласованных или оплаченных смет",
        )


def build_financial_document_number(
    prefix: str,
    estimate_id: int,
    issued_at: datetime,
) -> str:
    return f"{prefix}-{issued_at.strftime('%Y%m%d')}-{estimate_id:06d}"


def calculate_estimate_totals(estimate: Estimate) -> dict[str, float]:
    total_internal = (
        sum(
            (item.internal_price or 0) * (item.quantity or 0) for item in estimate.items
        )
        if estimate.use_internal_price
        else 0
    )
    total_external = sum(
        (item.external_price or 0) * (item.quantity or 0) for item in estimate.items
    )
    total_diff = total_external - total_internal if estimate.use_internal_price else 0
    vat = total_external * (estimate.vat_rate / 100) if estimate.vat_enabled else 0
    total_with_vat = total_external + vat
    return {
        "total_internal": total_internal,
        "total_external": total_external,
        "total_diff": total_diff,
        "vat": vat,
        "total_with_vat": total_with_vat,
    }


async def load_estimate_with_relations(
    db: AsyncSession,
    estimate_id: int,
    organization_id: int,
) -> Estimate:
    result = await db.execute(
        select(Estimate)
        .options(
            selectinload(Estimate.items),
            selectinload(Estimate.client),
            selectinload(Estimate.notes),
            selectinload(Estimate.user),
        )
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")
    return estimate


async def load_workspace_estimate(
    db: AsyncSession,
    estimate_id: int,
    organization_id: int,
) -> Estimate:
    result = await db.execute(
        select(Estimate).where(
            Estimate.id == estimate_id,
            Estimate.organization_id == organization_id,
        )
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    return estimate


async def load_estimate_approval_workflow(
    db: AsyncSession,
    estimate_id: int,
) -> EstimateApprovalWorkflow | None:
    result = await db.execute(
        select(EstimateApprovalWorkflow)
        .options(
            selectinload(EstimateApprovalWorkflow.steps).selectinload(
                EstimateApprovalStep.approver
            )
        )
        .where(EstimateApprovalWorkflow.estimate_id == estimate_id)
    )
    return result.scalar_one_or_none()


async def load_approvers_for_workflow(
    db: AsyncSession,
    approver_ids: list[int],
    organization_id: int,
):
    if not approver_ids:
        return {}

    query = (
        select(User.id, User.login, User.email, User.is_active)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .where(
            User.id.in_(approver_ids),
            OrganizationMembership.organization_id == organization_id,
        )
    )
    approvers_result = await db.execute(query)
    return {row.id: row for row in approvers_result.all()}


@router.post("/", response_model=EstimateOut)
async def create_estimate(
    estimate: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    await ensure_client_in_workspace(
        db,
        estimate.client_id,
        context.organization_id,
    )

    items_data = estimate.items or []
    new_estimate = Estimate(
        **estimate.dict(exclude={"items"}),
        user_id=user.id,
        organization_id=context.organization_id,
    )
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
    if new_estimate.client_id:
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


@router.put("/{estimate_id}", response_model=EstimateOut)
async def update_estimate(
    estimate_id: int,
    updated_data: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
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

    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    ensure_estimate_not_read_only(estimate)
    await ensure_estimate_not_in_active_approval(db, estimate.id)
    await ensure_client_in_workspace(
        db,
        updated_data.client_id,
        context.organization_id,
    )

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

    details = []
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

    if estimate.use_internal_price != updated_data.use_internal_price:
        details.append(
            "Включена внутренняя цена"
            if updated_data.use_internal_price
            else "Выключена внутренняя цена"
        )
    estimate.use_internal_price = updated_data.use_internal_price

    # Простые поля (кроме items, vat_enabled, vat_rate, use_internal_price)
    for field, value in updated_data.dict(
        exclude={"items", "vat_enabled", "vat_rate", "use_internal_price", "read_only"}
    ).items():
        old_val = getattr(estimate, field)
        actions = FIELD_ACTIONS_RU.get(field)

        if field == "status" and old_val != value:
            old_v = old_val.value if hasattr(old_val, "value") else str(old_val)
            new_v = value.value if hasattr(value, "value") else str(value)
            details.append(
                {
                    "label": actions["edit"] if actions else "Изменен статус",
                    "old": STATUS_LABELS_RU.get(old_v, old_v),
                    "new": STATUS_LABELS_RU.get(new_v, new_v),
                }
            )
            logger.info(
                f"Status changed from '{STATUS_LABELS_RU.get(old_v, old_v)}' to '{STATUS_LABELS_RU.get(new_v, new_v)}' for estimate {estimate_id} by user {user.id}"
            )

        elif actions:
            # Для полей, где разрешены add/del/edit (например, client_id)
            if "add" in actions and not old_val and value:
                # Добавили значение
                pretty_value = value
                if field == "client_id":
                    new_client = await db.get(Client, value) if value else None
                    pretty_value = new_client.name if new_client else value
                details.append(
                    {"label": actions["add"], "new": prettify_value(pretty_value)}
                )
            elif "del" in actions and old_val and not value:
                # Удалили значение
                pretty_value = old_val
                if field == "client_id":
                    old_client = await db.get(Client, old_val) if old_val else None
                    pretty_value = old_client.name if old_client else old_val
                details.append(
                    {"label": actions["del"], "old": prettify_value(pretty_value)}
                )
            elif "edit" in actions and old_val != value:
                # Изменили значение
                pretty_old = old_val
                pretty_new = value
                if field == "client_id":
                    old_client = await db.get(Client, old_val) if old_val else None
                    new_client = await db.get(Client, value) if value else None
                    pretty_old = old_client.name if old_client else old_val
                    pretty_new = new_client.name if new_client else value
                details.append(
                    {
                        "label": actions["edit"],
                        "old": prettify_value(pretty_old),
                        "new": prettify_value(pretty_new),
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
            details.append(
                {
                    "label": FIELD_ACTIONS_RU["service"]["add"],
                    "new": item.name,
                }
            )

    # Удалённые услуги (были раньше, но пропали)
    for item_id, item in old_items.items():
        if item_id not in [i.id for i in updated_data.items if i.id is not None]:
            details.append(
                {
                    "label": FIELD_ACTIONS_RU["service"]["del"],
                    "old": item.name,
                }
            )

    # Изменения в услугах
    for item_id, old_item in old_items.items():
        new_item = new_items.get(item_id)
        if new_item:
            for f in [
                "name",
                "description",
                "quantity",
                "unit",
                "internal_price",
                "external_price",
            ]:
                key = f"item_{f}"
                actions = FIELD_ACTIONS_RU.get(key)
                old_v = getattr(old_item, f, None)
                new_v = getattr(new_item, f, None)

                # Числовые поля — кастомный формат вывода
                if f in ["quantity", "internal_price", "external_price"]:
                    pretty_old = prettify_number(old_v)
                    pretty_new = prettify_number(new_v)
                else:
                    pretty_old = prettify_value(old_v)
                    pretty_new = prettify_value(new_v)

                if actions and old_v != new_v:
                    details.append(
                        {
                            "label": f"{actions['edit']} ({old_item.name})",
                            "old": pretty_old,
                            "new": pretty_new,
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
            action="Обновление сметы",
            description="Смета обновлена",
            details=details if details else None,
            timestamp=now,
        )
    )

    if estimate.client_id:
        db.add(
            ClientChangeLog(
                client_id=estimate.client_id,
                user_id=user.id,
                action="Обновление сметы",
                description=f"Обновлена смета: {estimate.name}",
                details=details if details else None,
                timestamp=now,
            )
        )

    await db.commit()

    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    return result.scalar_one()


@router.patch("/{estimate_id}/autosave")
async def autosave_estimate(
    estimate_id: int,
    payload: EstimateAutosave,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    ensure_estimate_not_read_only(estimate)
    await ensure_estimate_not_in_active_approval(db, estimate.id)
    data = payload.dict(exclude_unset=True)

    if "client_id" in data:
        await ensure_client_in_workspace(
            db,
            data["client_id"],
            context.organization_id,
        )
        estimate.client_id = data["client_id"]

    for field in (
        "name",
        "responsible",
        "event_datetime",
        "event_place",
        "status",
        "vat_enabled",
        "vat_rate",
        "use_internal_price",
    ):
        if field in data:
            setattr(estimate, field, data[field])

    if "items" in data:
        await db.execute(delete(EstimateItem).where(EstimateItem.estimate_id == estimate_id))
        for item in data["items"] or []:
            item_data = item if isinstance(item, dict) else item.dict()
            db.add(
                EstimateItem(
                    estimate_id=estimate_id,
                    name=item_data.get("name", ""),
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 0),
                    unit=item_data.get("unit", "шт"),
                    internal_price=item_data.get("internal_price", 0),
                    external_price=item_data.get("external_price", 0),
                    category=item_data.get("category", ""),
                )
            )

    await db.commit()
    await db.refresh(estimate)

    return {"detail": "Черновик сохранен", "updated_at": estimate.updated_at}


@router.patch("/{estimate_id}/read-only", response_model=EstimateOut)
async def set_estimate_read_only(
    estimate_id: int,
    payload: EstimateReadOnlyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    await ensure_estimate_not_in_active_approval(db, estimate.id)
    if estimate.read_only != payload.read_only:
        estimate.read_only = payload.read_only
        details = [
            {
                "label": "Режим редактирования",
                "new": "Только чтение" if payload.read_only else "Редактирование",
            }
        ]
        db.add(
            EstimateChangeLog(
                estimate_id=estimate.id,
                user_id=user.id,
                action="Изменение режима доступа",
                description=(
                    "Смета переведена в режим только чтение"
                    if payload.read_only
                    else "Смета переведена в режим редактирования"
                ),
                details=details,
            )
        )
        if estimate.client_id:
            db.add(
                ClientChangeLog(
                    client_id=estimate.client_id,
                    user_id=user.id,
                    action="Изменение режима доступа сметы",
                    description=f"Изменен режим доступа сметы: {estimate.name}",
                    details=details,
                )
            )
        await append_audit_ledger_entry(
            db,
            actor_user_id=user.id,
            action="estimate.read_only.changed",
            entity_type="estimate",
            entity_id=str(estimate.id),
            details={
                "estimate_name": estimate.name,
                "read_only": payload.read_only,
            },
            request=request,
        )
        await db.commit()

    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    return result.scalar_one()


@router.delete("/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_estimate(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()

    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    ensure_estimate_not_read_only(estimate)
    await ensure_estimate_not_in_active_approval(db, estimate.id)
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.deleted",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_name": estimate.name,
            "status": estimate.status.value if estimate.status else None,
        },
        request=request,
    )
    await db.delete(estimate)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{estimate_id}/favorite/", status_code=204)
async def add_favorite(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    # Проверяем, что смета существует и принадлежит этому пользователю
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate or estimate.organization_id != context.organization_id:
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
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
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


async def list_estimates(
    name: str = Query(None),
    client: Optional[int] = Query(None),  # Change type to Optional[int]
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    db: AsyncSession | None = None,
    context: WorkspaceContext | None = None,
    user=None,
    favorite: Optional[bool] = Query(None),
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database session is required")

    if context is not None:
        user_obj = context.user
        filters = [Estimate.organization_id == context.organization_id]
    else:
        # Backward compatibility for direct test calls.
        user_obj = user
        user_id = getattr(user_obj, "id", None)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Пользователь не аутентифицирован")
        filters = [Estimate.user_id == user_id]

    # Direct function calls in tests may pass FastAPI Query objects as defaults.
    # Normalize non-primitive placeholders to regular None values.
    if not isinstance(name, str):
        name = None
    if not isinstance(client, int):
        client = None
    if not isinstance(date_from, str):
        date_from = None
    if not isinstance(date_to, str):
        date_to = None
    if not isinstance(status, str):
        status = None
    if not isinstance(favorite, bool):
        favorite = None

    if name:
        filters.append(Estimate.name.ilike(f"%{name}%"))
    if client:
        filters.append(Estimate.client_id == client)
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            filters.append(Estimate.date >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            filters.append(Estimate.date < dt_to)
        except ValueError:
            pass

    if status:
        filters.append(Estimate.status == status)

    query = (
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(*filters)
    )
    count_query = select(func.count()).select_from(Estimate).where(*filters)
    if favorite:
        query = query.join(EstimateFavorite).where(EstimateFavorite.user_id == user_obj.id)
        count_query = count_query.join(EstimateFavorite).where(
            EstimateFavorite.user_id == user_obj.id
        )

    total = await db.scalar(count_query)

    result = await db.execute(
        query.order_by(Estimate.id.desc()).offset((page - 1) * limit).limit(limit)
    )

    estimates = result.scalars().all()

    # Получаем id всех избранных смет для текущего пользователя
    fav_result = await db.execute(
        select(EstimateFavorite.estimate_id).where(EstimateFavorite.user_id == user_obj.id)
    )
    favorite_ids = set(fav_result.scalars().all())

    for estimate in estimates:
        estimate.is_favorite = estimate.id in favorite_ids

    return {"items": estimates, "total": total}


@router.get("/", response_model=Paginated[EstimateOut])
async def list_estimates_endpoint(
    name: str = Query(None),
    client: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1),
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
    favorite: Optional[bool] = Query(None),
):
    return await list_estimates(
        name=name,
        client=client,
        date_from=date_from,
        date_to=date_to,
        status=status,
        page=page,
        limit=limit,
        db=db,
        context=context,
        favorite=favorite,
    )


@router.get("/{estimate_id}", response_model=EstimateOut)
async def get_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.items), selectinload(Estimate.client))
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.organization_id != context.organization_id:
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
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    result = await db.execute(select(Estimate).where(Estimate.id == estimate_id))
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")

    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой смете")

    count_q = (
        select(func.count())
        .select_from(EstimateChangeLog)
        .where(EstimateChangeLog.estimate_id == estimate_id)
    )
    total = await db.scalar(count_q)

    result = await db.execute(
        select(EstimateChangeLog)
        .options(selectinload(EstimateChangeLog.user))
        .where(EstimateChangeLog.estimate_id == estimate_id)
        .order_by(EstimateChangeLog.timestamp.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )

    items = [
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

    return {"items": items, "total": total}


@router.get("/{estimate_id}/approval-workflow", response_model=ApprovalWorkflowOut | None)
async def get_estimate_approval_workflow(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    await load_workspace_estimate(db, estimate_id, context.organization_id)
    workflow = await load_estimate_approval_workflow(db, estimate_id)
    if not workflow:
        return None
    return to_workflow_out(workflow)


@router.put("/{estimate_id}/approval-workflow", response_model=ApprovalWorkflowOut)
async def upsert_estimate_approval_workflow(
    estimate_id: int,
    payload: ApprovalWorkflowUpsertIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_APPROVAL_MANAGE)
    ),
):
    user = context.user
    estimate = await load_workspace_estimate(db, estimate_id, context.organization_id)
    ensure_estimate_not_read_only(estimate)

    workflow = await load_estimate_approval_workflow(db, estimate_id)
    if workflow and workflow.status == WORKFLOW_STATUS_IN_REVIEW:
        raise HTTPException(
            status_code=409,
            detail="Нельзя менять маршрут согласования, пока смета находится на согласовании",
        )
    approver_ids = sorted({step.approver_user_id for step in payload.steps})
    approvers_by_id = await load_approvers_for_workflow(
        db,
        approver_ids,
        context.organization_id,
    )

    for approver_id in approver_ids:
        row = approvers_by_id.get(approver_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Согласующий пользователь №{approver_id} не найден")
        if not row.is_active:
            raise HTTPException(
                status_code=409,
                detail=f"Согласующий пользователь №{approver_id} деактивирован",
            )

    if not workflow:
        workflow = EstimateApprovalWorkflow(
            estimate_id=estimate.id,
            owner_user_id=user.id,
            status=WORKFLOW_STATUS_DRAFT,
        )
        db.add(workflow)
        await db.flush()
    else:
        await db.execute(
            delete(EstimateApprovalStep).where(EstimateApprovalStep.workflow_id == workflow.id)
        )

    for step in payload.steps:
        db.add(
            EstimateApprovalStep(
                workflow_id=workflow.id,
                step_order=step.step_order,
                stage_key=step.stage_key,
                stage_label=step.stage_label,
                approver_user_id=step.approver_user_id,
                status=STEP_STATUS_PENDING,
            )
        )

    workflow.status = WORKFLOW_STATUS_DRAFT
    workflow.current_step_order = None
    workflow.started_at = None
    workflow.completed_at = None

    step_details = []
    for step in payload.steps:
        approver = approvers_by_id.get(step.approver_user_id)
        step_details.append(
            {
                "label": f"Шаг №{step.step_order}: {step.stage_label}",
                "new": f"{approver.login} ({approver.email})" if approver else str(step.approver_user_id),
            }
        )

    db.add(
        EstimateChangeLog(
            estimate_id=estimate.id,
            user_id=user.id,
            action="Маршрут согласования",
            description="Маршрут согласования обновлен",
            details=step_details,
        )
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.approval.workflow.updated",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={"estimate_name": estimate.name, "steps": step_details},
        request=request,
    )
    await db.commit()

    refreshed = await load_estimate_approval_workflow(db, estimate_id)
    return to_workflow_out(refreshed)


@router.post("/{estimate_id}/approval-workflow/start", response_model=ApprovalWorkflowOut)
async def start_estimate_approval_workflow(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_APPROVAL_MANAGE)
    ),
):
    user = context.user
    estimate = await load_workspace_estimate(db, estimate_id, context.organization_id)
    ensure_estimate_not_read_only(estimate)

    workflow = await load_estimate_approval_workflow(db, estimate_id)
    if not workflow or not workflow.steps:
        raise HTTPException(status_code=400, detail="Сначала настройте маршрут согласования")
    if workflow.status == WORKFLOW_STATUS_IN_REVIEW:
        raise HTTPException(status_code=409, detail="Согласование уже запущено")
    if any(step.approver_user_id is None for step in workflow.steps):
        raise HTTPException(
            status_code=409,
            detail="Для каждого шага согласования должен быть указан согласующий",
        )

    approver_ids = sorted(
        {step.approver_user_id for step in workflow.steps if step.approver_user_id is not None}
    )
    approver_state = await load_approvers_for_workflow(
        db,
        approver_ids,
        context.organization_id,
    )
    for approver_id in approver_ids:
        approver = approver_state.get(approver_id)
        if not approver or not approver.is_active:
            raise HTTPException(
                status_code=409,
                detail=f"Согласующий пользователь №{approver_id} недоступен",
            )

    for step in workflow.steps:
        step.status = STEP_STATUS_PENDING
        step.signed_at = None
        step.signature_name = None
        step.signature_hash = None
        step.decision = None
        step.decision_comment = None
        step.decided_by_user_id = None

    first_step = min(workflow.steps, key=lambda step: step.step_order)
    workflow.status = WORKFLOW_STATUS_IN_REVIEW
    workflow.current_step_order = first_step.step_order
    workflow.started_at = datetime.now(timezone.utc)
    workflow.completed_at = None
    if estimate.status == EstimateStatus.DRAFT:
        estimate.status = EstimateStatus.SENT

    db.add(
        EstimateChangeLog(
            estimate_id=estimate.id,
            user_id=user.id,
            action="Согласование",
            description="Запущен процесс согласования сметы",
            details=[
                {
                    "label": "Текущий шаг",
                    "new": f"{first_step.step_order}. {first_step.stage_label}",
                }
            ],
        )
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.approval.workflow.started",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_name": estimate.name,
            "current_step_order": workflow.current_step_order,
        },
        request=request,
    )
    await db.commit()

    refreshed = await load_estimate_approval_workflow(db, estimate_id)
    return to_workflow_out(refreshed)


@router.get("/{estimate_id}/export/pdf")
async def export_estimate_pdf(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    estimate = await load_estimate_with_relations(
        db,
        estimate_id,
        context.organization_id,
    )
    totals = calculate_estimate_totals(estimate)

    pdf_bytes = render_pdf(
        "estimate_pdf.html",
        {
            "estimate": estimate,
            **totals,
        },
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.export.pdf",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={"estimate_name": estimate.name},
        request=request,
    )
    await db.commit()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=estimate_{estimate.id}.pdf"
        },
    )


@router.get("/{estimate_id}/export/invoice-pdf")
async def export_estimate_invoice_pdf(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    estimate = await load_estimate_with_relations(
        db,
        estimate_id,
        context.organization_id,
    )
    ensure_financial_documents_allowed(estimate)
    totals = calculate_estimate_totals(estimate)
    issued_at = datetime.now(timezone.utc)
    invoice_number = build_financial_document_number("INV", estimate.id, issued_at)

    pdf_bytes = render_pdf(
        "invoice_pdf.html",
        {
            "estimate": estimate,
            "invoice_number": invoice_number,
            "issue_date": issued_at,
            **totals,
        },
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.export.invoice_pdf",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_name": estimate.name,
            "invoice_number": invoice_number,
        },
        request=request,
    )
    await db.commit()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{estimate.id}.pdf"
        },
    )


@router.get("/{estimate_id}/export/act-pdf")
async def export_estimate_act_pdf(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    estimate = await load_estimate_with_relations(
        db,
        estimate_id,
        context.organization_id,
    )
    ensure_financial_documents_allowed(estimate)
    totals = calculate_estimate_totals(estimate)
    issued_at = datetime.now(timezone.utc)
    act_number = build_financial_document_number("ACT", estimate.id, issued_at)

    pdf_bytes = render_pdf(
        "act_pdf.html",
        {
            "estimate": estimate,
            "act_number": act_number,
            "issue_date": issued_at,
            **totals,
        },
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.export.act_pdf",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_name": estimate.name,
            "act_number": act_number,
        },
        request=request,
    )
    await db.commit()
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=act_{estimate.id}.pdf"},
    )


@router.post("/{estimate_id}/send-email")
async def send_estimate_email(
    estimate_id: int,
    payload: EstimateSendEmail,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_EDIT)
    ),
):
    user = context.user
    if not payload.attach_pdf and not payload.attach_excel:
        raise HTTPException(
            status_code=422,
            detail="Необходимо выбрать хотя бы один формат вложения (PDF или Excel)",
        )

    estimate = await load_estimate_with_relations(
        db,
        estimate_id,
        context.organization_id,
    )

    attachments: List[EmailAttachment] = []
    if payload.attach_pdf:
        totals = calculate_estimate_totals(estimate)

        pdf_bytes = render_pdf(
            "estimate_pdf.html",
            {
                "estimate": estimate,
                **totals,
            },
        )
        attachments.append(
            {
                "filename": f"estimate_{estimate.id}.pdf",
                "content": pdf_bytes,
                "content_type": "application/pdf",
            }
        )

    if payload.attach_excel:
        excel_file = generate_excel(estimate)
        attachments.append(
            {
                "filename": f"estimate_{estimate.id}.xlsx",
                "content": excel_file.getvalue(),
                "content_type": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            }
        )

    subject = payload.subject or f"Смета: {estimate.name}"
    try:
        await send_email(
            subject=subject,
            body=payload.message,
            to=payload.to,
            attachments=attachments,
        )
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Не удалось отправить письмо со сметой")

    db.add(
        EstimateChangeLog(
            estimate_id=estimate.id,
            user_id=user.id,
            action="Отправка",
            description=f"Смета отправлена на {payload.to}",
            details=[
                {
                    "label": "Вложения",
                    "new": ", ".join(a["filename"] for a in attachments),
                }
            ],
        )
    )
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.send_email",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_name": estimate.name,
            "to": payload.to,
            "attachments": [a["filename"] for a in attachments],
        },
        request=request,
    )
    await db.commit()

    return {"detail": "Смета успешно отправлена"}


@router.get("/{estimate_id}/export/excel")
async def export_estimate_excel(
    estimate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_DATA_VIEW)
    ),
):
    user = context.user
    result = await db.execute(
        select(Estimate)
        .options(
            selectinload(Estimate.items),
            selectinload(Estimate.client),
            selectinload(Estimate.notes),
        )
        .where(Estimate.id == estimate_id)
    )
    estimate = result.scalar_one_or_none()

    if not estimate or estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=404, detail="Смета не найдена или нет доступа")

    filename = f"{estimate.name}.xlsx"
    ascii_filename = re.sub(r"[^\x00-\x7F]+", "_", filename)
    utf8_filename = quote(filename)

    excel_file = generate_excel(estimate)
    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.export.excel",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={"estimate_name": estimate.name, "filename": filename},
        request=request,
    )
    await db.commit()
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={ascii_filename}; filename*=UTF-8''{utf8_filename}"
        },
    )
