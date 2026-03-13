from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.changelog import EstimateChangeLog
from app.models.estimate import Estimate, EstimateStatus
from app.models.estimate_approval import EstimateApprovalStep, EstimateApprovalWorkflow
from app.schemas.approval import (
    ApprovalDecisionIn,
    ApprovalEstimatePreviewOut,
    ApprovalWorkflowOut,
    MyApprovalTaskOut,
)
from app.services.approval_workflow import (
    STEP_STATUS_APPROVED,
    STEP_STATUS_PENDING,
    STEP_STATUS_REJECTED,
    WORKFLOW_STATUS_APPROVED,
    WORKFLOW_STATUS_IN_REVIEW,
    WORKFLOW_STATUS_REJECTED,
    build_esign_hash,
    get_next_pending_step,
    to_workflow_out,
)
from app.services.audit_ledger import append_audit_ledger_entry
from app.utils.auth import get_current_user
from app.utils.workspace import (
    WORKSPACE_PERMISSION_APPROVAL_SIGN,
    WorkspaceContext,
    require_workspace_permission,
)

router = APIRouter(tags=["approvals"], dependencies=[Depends(get_current_user)])


def _calculate_totals(estimate: Estimate) -> tuple[float, float]:
    total_external = float(
        sum((item.external_price or 0) * (item.quantity or 0) for item in estimate.items or [])
    )
    vat = total_external * (estimate.vat_rate / 100) if estimate.vat_enabled else 0
    total_with_vat = total_external + vat
    return round(total_external, 2), round(total_with_vat, 2)


@router.get("/my", response_model=list[MyApprovalTaskOut])
async def get_my_approval_tasks(
    scope: str = Query(default="pending", pattern="^(pending|history|all)$"),
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_APPROVAL_SIGN)
    ),
):
    user = context.user
    query = (
        select(EstimateApprovalStep)
        .join(
            EstimateApprovalWorkflow,
            EstimateApprovalWorkflow.id == EstimateApprovalStep.workflow_id,
        )
        .join(Estimate, Estimate.id == EstimateApprovalWorkflow.estimate_id)
        .options(
            selectinload(EstimateApprovalStep.workflow)
            .selectinload(EstimateApprovalWorkflow.estimate)
            .selectinload(Estimate.client),
            selectinload(EstimateApprovalStep.workflow)
            .selectinload(EstimateApprovalWorkflow.estimate)
            .selectinload(Estimate.user),
            selectinload(EstimateApprovalStep.workflow)
            .selectinload(EstimateApprovalWorkflow.estimate)
            .selectinload(Estimate.items),
        )
        .where(
            EstimateApprovalStep.approver_user_id == user.id,
            Estimate.organization_id == context.organization_id,
        )
    )

    if scope == "pending":
        query = query.where(
            EstimateApprovalWorkflow.status == WORKFLOW_STATUS_IN_REVIEW,
            EstimateApprovalStep.status == STEP_STATUS_PENDING,
            EstimateApprovalStep.step_order == EstimateApprovalWorkflow.current_step_order,
        ).order_by(EstimateApprovalWorkflow.started_at.asc())
    elif scope == "history":
        query = query.where(
            EstimateApprovalStep.status.in_([STEP_STATUS_APPROVED, STEP_STATUS_REJECTED])
        ).order_by(EstimateApprovalStep.signed_at.desc())
    else:
        query = query.order_by(EstimateApprovalStep.id.desc())

    result = await db.execute(query)
    steps = result.scalars().all()

    response: list[MyApprovalTaskOut] = []
    for step in steps:
        workflow = step.workflow
        if not workflow or not workflow.estimate:
            continue
        estimate = workflow.estimate
        total_external, total_with_vat = _calculate_totals(estimate)
        items_preview = [
            f"{item.name} ({item.quantity} {item.unit})"
            for item in sorted(estimate.items or [], key=lambda i: i.id or 0)[:3]
        ]
        response.append(
            MyApprovalTaskOut(
                step_id=step.id,
                workflow_id=workflow.id,
                estimate_id=estimate.id,
                estimate_name=estimate.name,
                estimate_status=estimate.status.value if estimate.status else "draft",
                estimate_owner_id=estimate.user_id,
                estimate_owner_login=estimate.user.login if estimate.user else None,
                client_name=estimate.client.name if estimate.client else None,
                step_order=step.step_order,
                stage_key=step.stage_key,
                stage_label=step.stage_label,
                step_status=step.status,
                workflow_status=workflow.status,
                started_at=workflow.started_at,
                responsible=estimate.responsible,
                event_datetime=estimate.event_datetime,
                total_external=total_external,
                total_with_vat=total_with_vat,
                items_preview=items_preview,
                can_open_estimate=True,
            )
        )
    return response


@router.get("/estimates/{estimate_id}/preview", response_model=ApprovalEstimatePreviewOut)
async def get_approval_estimate_preview(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_APPROVAL_SIGN)
    ),
):
    user = context.user
    estimate_result = await db.execute(
        select(Estimate)
        .options(
            selectinload(Estimate.client),
            selectinload(Estimate.items),
        )
        .where(Estimate.id == estimate_id)
    )
    estimate = estimate_result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(status_code=404, detail="Смета не найдена")
    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к предпросмотру сметы")

    access_result = await db.execute(
        select(EstimateApprovalStep.id)
        .join(
            EstimateApprovalWorkflow,
            EstimateApprovalWorkflow.id == EstimateApprovalStep.workflow_id,
        )
        .where(
            EstimateApprovalWorkflow.estimate_id == estimate_id,
            EstimateApprovalStep.approver_user_id == user.id,
        )
        .limit(1)
    )
    if access_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Нет доступа к предпросмотру сметы")

    total_external, total_with_vat = _calculate_totals(estimate)
    items_preview = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "external_price": item.external_price,
            "line_total": round((item.quantity or 0) * (item.external_price or 0), 2),
        }
        for item in sorted(estimate.items or [], key=lambda i: i.id or 0)[:8]
    ]
    return ApprovalEstimatePreviewOut(
        estimate_id=estimate.id,
        name=estimate.name,
        status=estimate.status.value if estimate.status else "draft",
        client_name=estimate.client.name if estimate.client else None,
        responsible=estimate.responsible,
        event_datetime=estimate.event_datetime,
        event_place=estimate.event_place,
        total_external=total_external,
        total_with_vat=total_with_vat,
        vat_enabled=bool(estimate.vat_enabled),
        vat_rate=int(estimate.vat_rate or 0),
        read_only=bool(estimate.read_only),
        items_preview=items_preview,
        can_open_estimate=True,
    )


@router.post("/steps/{step_id}/decision", response_model=ApprovalWorkflowOut)
async def sign_approval_step(
    step_id: int,
    payload: ApprovalDecisionIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    context: WorkspaceContext = Depends(
        require_workspace_permission(WORKSPACE_PERMISSION_APPROVAL_SIGN)
    ),
):
    user = context.user
    result = await db.execute(
        select(EstimateApprovalStep)
        .options(
            selectinload(EstimateApprovalStep.workflow)
            .selectinload(EstimateApprovalWorkflow.steps)
            .selectinload(EstimateApprovalStep.approver),
            selectinload(EstimateApprovalStep.workflow).selectinload(
                EstimateApprovalWorkflow.estimate
            ),
        )
        .where(EstimateApprovalStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step or not step.workflow or not step.workflow.estimate:
        raise HTTPException(status_code=404, detail="Шаг согласования не найден")

    workflow = step.workflow
    estimate = workflow.estimate
    if estimate.organization_id != context.organization_id:
        raise HTTPException(status_code=403, detail="Нет доступа к шагу согласования")

    if step.approver_user_id != user.id:
        raise HTTPException(status_code=403, detail="Вы не назначены на этот шаг согласования")
    if workflow.status != WORKFLOW_STATUS_IN_REVIEW:
        raise HTTPException(status_code=409, detail="Процесс согласования не активен")
    if step.status != STEP_STATUS_PENDING:
        raise HTTPException(status_code=409, detail="Шаг уже подписан")
    if step.step_order != workflow.current_step_order:
        raise HTTPException(status_code=409, detail="Сейчас активен другой шаг согласования")

    signed_at = datetime.now(timezone.utc)
    step.signature_name = payload.signature_name
    step.signature_hash = build_esign_hash(
        workflow_id=workflow.id,
        step_id=step.id,
        approver_user_id=user.id,
        decision=payload.decision,
        signature_name=payload.signature_name,
        signed_at=signed_at,
    )
    step.signed_at = signed_at
    step.decision_comment = payload.comment
    step.decided_by_user_id = user.id
    step.decision = payload.decision
    step.status = (
        STEP_STATUS_APPROVED if payload.decision == "approve" else STEP_STATUS_REJECTED
    )

    if payload.decision == "approve":
        next_step = get_next_pending_step(workflow)
        if next_step:
            workflow.current_step_order = next_step.step_order
        else:
            workflow.status = WORKFLOW_STATUS_APPROVED
            workflow.completed_at = signed_at
            workflow.current_step_order = None
            estimate.status = EstimateStatus.APPROVED
    else:
        workflow.status = WORKFLOW_STATUS_REJECTED
        workflow.completed_at = signed_at
        workflow.current_step_order = None
        estimate.status = EstimateStatus.CANCELLED

    status_text = "согласован" if payload.decision == "approve" else "отклонен"
    db.add(
        EstimateChangeLog(
            estimate_id=estimate.id,
            user_id=user.id,
            action="Согласование",
            description=f"Шаг «{step.stage_label}» {status_text}",
            details=[
                {"label": "Подпись", "new": step.signature_name},
                {"label": "Решение", "new": "Одобрено" if payload.decision == "approve" else "Отклонено"},
                {"label": "Комментарий", "new": payload.comment or "—"},
            ],
        )
    )

    await append_audit_ledger_entry(
        db,
        actor_user_id=user.id,
        action="estimate.approval.step.signed",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "workflow_id": workflow.id,
            "step_id": step.id,
            "step_order": step.step_order,
            "stage_key": step.stage_key,
            "stage_label": step.stage_label,
            "decision": payload.decision,
            "signature_hash": step.signature_hash,
        },
        request=request,
    )
    await db.commit()

    refreshed = await db.execute(
        select(EstimateApprovalWorkflow)
        .options(
            selectinload(EstimateApprovalWorkflow.steps).selectinload(
                EstimateApprovalStep.approver
            )
        )
        .where(EstimateApprovalWorkflow.id == workflow.id)
    )
    workflow_refreshed = refreshed.scalar_one()
    return to_workflow_out(workflow_refreshed)
