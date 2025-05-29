## backend/app/schemas/estimate.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.item import EstimateItemOut, EstimateItemCreate
from app.models.estimate import EstimateStatus
from app.schemas.client import ClientOut


class EstimateBase(BaseModel):
    name: str = Field(..., min_length=1)
    client_id: int
    responsible: str = Field(..., min_length=1)
    notes: Optional[str]
    status: EstimateStatus = EstimateStatus.DRAFT
    vat_enabled: bool = True
    vat_rate: int = 20


class EstimateCreate(EstimateBase):
    pass
    items: Optional[List[EstimateItemCreate]] = []

    @validator("items")
    def must_have_at_least_one_item(cls, v):
        if not v:
            raise ValueError("Смета должна содержать хотя бы одну услугу")
        return v
    
    @validator('vat_rate')
    def check_vat_rate(cls, v):
        if not isinstance(v, int) or v < 0 or v > 100:
            raise ValueError("Ставка НДС должна быть целым числом от 0 до 100")
        return v


class EstimateOut(EstimateBase):
    id: int
    date: datetime
    updated_at: Optional[datetime] = None
    items: List[EstimateItemOut] = Field(..., min_items=1)
    vat_enabled: bool = True
    vat_rate: int
    user_id: int
    client: Optional[ClientOut]
    status: EstimateStatus
    model_config = {"from_attributes": True}
