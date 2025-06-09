from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ChangeDetail(BaseModel):
    label: str
    old: Optional[str] = None
    new: Optional[str] = None


class ChangeLogOut(BaseModel):
    id: int
    action: str
    description: str
    details: Optional[List[Union[str, ChangeDetail]]] = None
    timestamp: Optional[datetime] = None
    user_id: int
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}
