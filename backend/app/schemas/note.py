from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NoteBase(BaseModel):
    text: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteOut(NoteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int
    user_name: Optional[str] = None

    model_config = {"from_attributes": True}
