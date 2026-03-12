## backend/app/schemas/estimate.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.estimate import EstimateStatus
from app.schemas.client import ClientOut
from app.schemas.item import EstimateItemCreate, EstimateItemOut, EstimateItemUpdate


class EstimateBase(BaseModel):
    name: str = Field(..., min_length=1)
    client_id: Optional[int] = None
    responsible: str = Field(..., min_length=1)
    event_datetime: Optional[datetime]
    event_place: Optional[str]
    status: EstimateStatus = EstimateStatus.DRAFT
    vat_enabled: bool = True
    vat_rate: int = 20
    use_internal_price: bool = True
    read_only: bool = False


class EstimateCreate(EstimateBase):
    items: Optional[List[EstimateItemCreate]] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def must_have_at_least_one_item(cls, value):
        if not value:
            raise ValueError("Смета должна содержать хотя бы одну услугу")
        return value

    @field_validator("vat_rate")
    @classmethod
    def check_vat_rate(cls, value):
        if not isinstance(value, int) or value < 0 or value > 100:
            raise ValueError("Ставка НДС должна быть целым числом от 0 до 100")
        return value


class EstimateUpdate(EstimateBase):
    items: Optional[List[EstimateItemUpdate]] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def must_have_at_least_one_item(cls, value):
        if not value:
            raise ValueError("Смета должна содержать хотя бы одну услугу")
        return value

    @field_validator("vat_rate")
    @classmethod
    def check_vat_rate(cls, value):
        if not isinstance(value, int) or value < 0 or value > 100:
            raise ValueError("Ставка НДС должна быть целым числом от 0 до 100")
        return value


class EstimateOut(EstimateBase):
    id: int
    date: datetime
    updated_at: Optional[datetime] = None
    items: List[EstimateItemOut] = Field(..., min_length=1)
    vat_enabled: bool = True
    vat_rate: int
    use_internal_price: bool = True
    user_id: int
    client: Optional[ClientOut]
    status: EstimateStatus
    is_favorite: Optional[bool] = False
    model_config = {"from_attributes": True}


class EstimateSendEmail(BaseModel):
    to: EmailStr
    subject: Optional[str] = Field(default=None, min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    attach_pdf: bool = True
    attach_excel: bool = True


class EstimateItemAutosave(BaseModel):
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    quantity: float = 0
    unit: str = "шт"
    internal_price: float = 0
    external_price: float = 0
    category: str = ""


class EstimateAutosave(BaseModel):
    name: Optional[str] = None
    client_id: Optional[int] = None
    responsible: Optional[str] = None
    event_datetime: Optional[datetime] = None
    event_place: Optional[str] = None
    status: Optional[EstimateStatus] = None
    vat_enabled: Optional[bool] = None
    vat_rate: Optional[int] = None
    use_internal_price: Optional[bool] = None
    items: Optional[List[EstimateItemAutosave]] = None


class EstimateReadOnlyUpdate(BaseModel):
    read_only: bool
