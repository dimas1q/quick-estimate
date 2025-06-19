## backend/app/schemas/client.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


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
