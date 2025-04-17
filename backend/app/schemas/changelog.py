from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChangeLogOut(BaseModel):
    id: int
    action: str
    description: str
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}
