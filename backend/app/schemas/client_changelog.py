## backend/app/schemas/client_changelog.py

from datetime import datetime
from typing import Optional, List, Union

from pydantic import BaseModel


class ChangeDetail(BaseModel):
    label: str
    old: str
    new: str

class ClientChangeLogOut(BaseModel):
    id: int
    action: str
    description: str
    details: Optional[List[Union[str, ChangeDetail]]] = None
    timestamp: Optional[datetime] = None
    user_id: int
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}
