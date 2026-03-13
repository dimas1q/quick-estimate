from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ApprovalStepConfigIn(BaseModel):
    step_order: int = Field(..., ge=1, le=20)
    stage_key: str = Field(..., min_length=2, max_length=40)
    stage_label: str = Field(..., min_length=2, max_length=80)
    approver_user_id: int = Field(..., ge=1)

    @field_validator("stage_key")
    @classmethod
    def normalize_stage_key(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    @field_validator("stage_label")
    @classmethod
    def normalize_stage_label(cls, value: str) -> str:
        return value.strip()


class ApprovalWorkflowUpsertIn(BaseModel):
    steps: list[ApprovalStepConfigIn] = Field(..., min_length=1, max_length=20)

    @field_validator("steps")
    @classmethod
    def validate_unique_order(cls, value: list[ApprovalStepConfigIn]):
        orders = [item.step_order for item in value]
        if len(set(orders)) != len(orders):
            raise ValueError("Порядок шагов должен быть уникальным")
        return sorted(value, key=lambda item: item.step_order)


class ApprovalStepOut(BaseModel):
    id: int
    step_order: int
    stage_key: str
    stage_label: str
    approver_user_id: int | None
    approver_login: str | None
    approver_email: str | None
    status: str
    decision: str | None
    decision_comment: str | None
    signature_name: str | None
    signature_hash: str | None
    signed_at: datetime | None
    decided_by_user_id: int | None


class ApprovalWorkflowOut(BaseModel):
    id: int
    estimate_id: int
    owner_user_id: int
    status: str
    current_step_order: int | None
    started_at: datetime | None
    completed_at: datetime | None
    steps: list[ApprovalStepOut] = Field(default_factory=list)


class ApprovalDecisionIn(BaseModel):
    decision: Literal["approve", "reject"]
    signature_name: str = Field(..., min_length=2, max_length=120)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("signature_name")
    @classmethod
    def normalize_signature_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class MyApprovalTaskOut(BaseModel):
    step_id: int
    workflow_id: int
    estimate_id: int
    estimate_name: str
    estimate_status: str
    estimate_owner_id: int
    estimate_owner_login: str | None
    client_name: str | None
    step_order: int
    stage_key: str
    stage_label: str
    step_status: str
    workflow_status: str
    started_at: datetime | None
    due_hint: str | None = None
    responsible: str | None = None
    event_datetime: datetime | None = None
    total_external: float = 0
    total_with_vat: float = 0
    items_preview: list[str] = Field(default_factory=list)
    can_open_estimate: bool = False


class ApprovalEstimatePreviewOut(BaseModel):
    estimate_id: int
    name: str
    status: str
    client_name: str | None = None
    responsible: str | None = None
    event_datetime: datetime | None = None
    event_place: str | None = None
    total_external: float = 0
    total_with_vat: float = 0
    vat_enabled: bool
    vat_rate: int
    read_only: bool
    items_preview: list[dict] = Field(default_factory=list)
    can_open_estimate: bool = False
