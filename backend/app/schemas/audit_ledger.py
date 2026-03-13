from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLedgerOut(BaseModel):
    id: int
    occurred_at: datetime
    actor_user_id: int | None
    actor_login: str | None
    actor_email: str | None

    action: str
    entity_type: str
    entity_id: str | None

    request_method: str | None
    request_path: str | None
    ip_address: str | None
    user_agent: str | None

    details: Any
    prev_hash: str
    entry_hash: str


class AuditLedgerVerifyOut(BaseModel):
    is_valid: bool
    checked_entries: int
    broken_entry_id: int | None = None
    reason: str | None = None
    expected_hash: str | None = None
    actual_hash: str | None = None
    latest_hash: str | None = None
