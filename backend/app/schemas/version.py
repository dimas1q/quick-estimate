# backend/app/schemas/version.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict


class VersionOut(BaseModel):
    id: int
    estimate_id: int
    version: int
    created_at: datetime
    user_id: int
    payload: Dict[str, Any]

    model_config = {"from_attributes": True}
