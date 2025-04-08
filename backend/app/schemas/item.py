from pydantic import BaseModel
from typing import Optional

class EstimateItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: float
    unit: str
    unit_price: float
    discount: float
    discount_type: str  # "percent" or "fixed"
    category: Optional[str] = None

class EstimateItemCreate(EstimateItemBase):
    pass

class EstimateItemOut(EstimateItemBase):
    id: int

    class Config:
        orm_mode = True
