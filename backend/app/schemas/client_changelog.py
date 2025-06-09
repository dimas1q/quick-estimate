## backend/app/schemas/client_changelog.py

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ClientChangeLogOut(BaseModel):
    id: int
    action: str
    description: str
    details: Optional[List[str]] = None  # <-- добавить!
    timestamp: Optional[datetime] = None
    user_id: int
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}
