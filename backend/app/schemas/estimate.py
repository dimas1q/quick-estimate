from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.item import EstimateItemOut, EstimateItemCreate

class EstimateBase(BaseModel):
    name: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    client_company: str = Field(..., min_length=1)
    client_contact: Optional[str]
    responsible: Optional[str]
    notes: Optional[str]

class EstimateCreate(EstimateBase):
    pass
    items: Optional[List[EstimateItemCreate]] = []
    vat_enabled: bool = True

    @validator("items")
    def must_have_at_least_one_item(cls, v):
        if not v:
            raise ValueError("Смета должна содержать хотя бы одну услугу")
        return v


class EstimateOut(EstimateBase):
    id: int
    date: datetime
    updated_at: Optional[datetime] = None
    items: List[EstimateItemOut] = Field(..., min_items=1)
    vat_enabled: bool = True
    user_id: int
    model_config = {"from_attributes": True}
