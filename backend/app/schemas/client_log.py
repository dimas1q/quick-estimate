from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClientLogCreate(BaseModel):
    action: str
    description: str


class ClientLogOut(BaseModel):
    id: int
    action: str
    description: str
    timestamp: Optional[datetime] = None
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}
