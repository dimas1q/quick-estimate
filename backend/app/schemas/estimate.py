from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.item import EstimateItemOut, EstimateItemCreate

class EstimateBase(BaseModel):
    name: str
    client_name: Optional[str]
    client_company: Optional[str]
    client_contact: Optional[str]
    responsible: Optional[str]
    notes: Optional[str]

class EstimateCreate(EstimateBase):
    pass
    items: Optional[List[EstimateItemCreate]] = []
    vat_enabled: bool = True

class EstimateOut(EstimateBase):
    id: int
    date: datetime
    updated_at: Optional[datetime] = None
    items: List[EstimateItemOut]
    vat_enabled: bool = True
    class Config:
        orm_mode = True
