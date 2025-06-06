from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClientChangeLogOut(BaseModel):
    id: int
    action: str
    description: str
    timestamp: Optional[datetime] = None
    user_id: int
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}
