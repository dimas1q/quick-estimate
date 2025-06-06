from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClientLogCreate(BaseModel):
    action: str
    description: Optional[str] = None
    estimate_id: Optional[int] = None


class ClientLogOut(ClientLogCreate):
    id: int
    client_id: int
    user_id: int
    timestamp: datetime

    model_config = {"from_attributes": True}
