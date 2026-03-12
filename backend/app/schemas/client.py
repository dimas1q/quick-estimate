## backend/app/schemas/client.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from app.models.client import ClientPipelineStage
from app.models.estimate import EstimateStatus


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1)
    company: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    legal_address: Optional[str]
    actual_address: Optional[str]
    inn: Optional[str]
    kpp: Optional[str]
    bik: Optional[str]
    account: Optional[str]
    bank: Optional[str]
    corr_account: Optional[str]
    pipeline_stage: ClientPipelineStage = ClientPipelineStage.LEAD
    pipeline_expected_revenue: float = Field(default=0, ge=0)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ClientPipelineUpdate(BaseModel):
    pipeline_stage: Optional[ClientPipelineStage] = None
    pipeline_expected_revenue: Optional[float] = Field(default=None, ge=0)


class ClientPipelineSummary(BaseModel):
    lead_count: int
    quote_count: int
    approved_count: int
    paid_count: int
    total_expected_revenue: float
    weighted_forecast: float


class ClientPipelineItem(BaseModel):
    id: int
    name: str
    company: Optional[str]
    pipeline_stage: ClientPipelineStage
    pipeline_expected_revenue: float
    forecast_amount: float
    estimates_count: int
    last_estimate_date: Optional[datetime]
    last_estimate_status: Optional[EstimateStatus]
    open_revenue: float
    paid_revenue: float


class ClientPipelineOut(BaseModel):
    summary: ClientPipelineSummary
    items: list[ClientPipelineItem]
