# backend/app/schemas/item.py
from pydantic import BaseModel, Field
from typing import Optional


class EstimateItemBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""
    quantity: float = Field(..., gt=0)
    unit: str
    internal_price: float = Field(..., gt=0)
    external_price: float = Field(..., gt=0)
    category: str = ""


class EstimateItemCreate(EstimateItemBase):
    pass


class EstimateItemOut(EstimateItemBase):
    id: int
    model_config = {"from_attributes": True}


class EstimateItemUpdate(EstimateItemBase):
    id: Optional[int] = None  # <-- ключевое отличие!
