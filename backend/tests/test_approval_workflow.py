from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.approval_workflow import (
    STEP_STATUS_APPROVED,
    STEP_STATUS_PENDING,
    build_esign_hash,
    get_next_pending_step,
)


def test_esign_hash_is_deterministic():
    signed_at = datetime(2026, 3, 13, 6, 30, 0, tzinfo=timezone.utc)
    first = build_esign_hash(
        workflow_id=10,
        step_id=3,
        approver_user_id=5,
        decision="approve",
        signature_name="Иван Петров",
        signed_at=signed_at,
    )
    second = build_esign_hash(
        workflow_id=10,
        step_id=3,
        approver_user_id=5,
        decision="approve",
        signature_name="Иван Петров",
        signed_at=signed_at,
    )

    assert first == second
    assert len(first) == 64


def test_get_next_pending_step_returns_lowest_pending_order():
    workflow = SimpleNamespace(
        steps=[
            SimpleNamespace(step_order=2, status=STEP_STATUS_PENDING),
            SimpleNamespace(step_order=1, status=STEP_STATUS_APPROVED),
            SimpleNamespace(step_order=3, status=STEP_STATUS_PENDING),
        ]
    )

    next_step = get_next_pending_step(workflow)

    assert next_step is not None
    assert next_step.step_order == 2
