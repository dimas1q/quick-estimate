import hashlib
import hmac
from datetime import datetime, timezone

from app.core.config import settings
from app.models.estimate_approval import EstimateApprovalStep, EstimateApprovalWorkflow
from app.schemas.approval import ApprovalStepOut, ApprovalWorkflowOut


WORKFLOW_STATUS_DRAFT = "draft"
WORKFLOW_STATUS_IN_REVIEW = "in_review"
WORKFLOW_STATUS_APPROVED = "approved"
WORKFLOW_STATUS_REJECTED = "rejected"

STEP_STATUS_PENDING = "pending"
STEP_STATUS_APPROVED = "approved"
STEP_STATUS_REJECTED = "rejected"


def build_esign_hash(
    *,
    workflow_id: int,
    step_id: int,
    approver_user_id: int,
    decision: str,
    signature_name: str,
    signed_at: datetime,
) -> str:
    secret = (settings.JWT_SECRET_KEY or "quickestimate-dev-secret").encode("utf-8")
    material = (
        f"{workflow_id}|{step_id}|{approver_user_id}|"
        f"{decision}|{signature_name}|{signed_at.astimezone(timezone.utc).isoformat()}"
    )
    return hmac.new(secret, material.encode("utf-8"), hashlib.sha256).hexdigest()


def to_workflow_out(workflow: EstimateApprovalWorkflow) -> ApprovalWorkflowOut:
    steps = [
        ApprovalStepOut(
            id=step.id,
            step_order=step.step_order,
            stage_key=step.stage_key,
            stage_label=step.stage_label,
            approver_user_id=step.approver_user_id,
            approver_login=step.approver.login if step.approver else None,
            approver_email=step.approver.email if step.approver else None,
            status=step.status,
            decision=step.decision,
            decision_comment=step.decision_comment,
            signature_name=step.signature_name,
            signature_hash=step.signature_hash,
            signed_at=step.signed_at,
            decided_by_user_id=step.decided_by_user_id,
        )
        for step in workflow.steps
    ]
    return ApprovalWorkflowOut(
        id=workflow.id,
        estimate_id=workflow.estimate_id,
        owner_user_id=workflow.owner_user_id,
        status=workflow.status,
        current_step_order=workflow.current_step_order,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        steps=steps,
    )


def get_next_pending_step(
    workflow: EstimateApprovalWorkflow,
) -> EstimateApprovalStep | None:
    pending = [step for step in workflow.steps if step.status == STEP_STATUS_PENDING]
    if not pending:
        return None
    return min(pending, key=lambda step: step.step_order)
