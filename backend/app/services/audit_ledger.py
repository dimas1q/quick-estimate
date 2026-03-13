import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_ledger import AuditLedgerEntry

GENESIS_HASH = "0" * 64


@dataclass
class AuditChainVerification:
    is_valid: bool
    checked_entries: int
    broken_entry_id: int | None
    reason: str | None
    expected_hash: str | None
    actual_hash: str | None
    latest_hash: str | None


def _normalize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _canonical_payload(entry_payload: dict[str, Any]) -> str:
    return json.dumps(
        entry_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def build_audit_hash_payload(
    *,
    occurred_at: datetime,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    request_method: str | None,
    request_path: str | None,
    ip_address: str | None,
    user_agent: str | None,
    details: Any,
) -> dict[str, Any]:
    return {
        "occurred_at": _normalize_datetime(occurred_at),
        "actor_user_id": actor_user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "request_method": request_method,
        "request_path": request_path,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": jsonable_encoder(details if details is not None else {}),
    }


def compute_audit_entry_hash(*, prev_hash: str, payload: dict[str, Any]) -> str:
    material = f"{prev_hash}|{_canonical_payload(payload)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def extract_request_metadata(request: Request | None) -> dict[str, str | None]:
    if request is None:
        return {
            "request_method": None,
            "request_path": None,
            "ip_address": None,
            "user_agent": None,
        }

    forwarded_for = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    client_ip = forwarded_for or (request.client.host if request.client else None)

    return {
        "request_method": request.method[:16] if request.method else None,
        "request_path": str(request.url.path)[:512] if request.url.path else None,
        "ip_address": client_ip[:128] if client_ip else None,
        "user_agent": (request.headers.get("User-Agent") or "")[:512] or None,
    }


async def _lock_ledger_for_append(db: AsyncSession) -> None:
    dialect_name = db.bind.dialect.name if db.bind is not None else ""
    if dialect_name == "postgresql":
        await db.execute(text("LOCK TABLE audit_ledger_entries IN EXCLUSIVE MODE"))


async def append_audit_ledger_entry(
    db: AsyncSession,
    *,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: Any = None,
    request: Request | None = None,
) -> AuditLedgerEntry:
    await _lock_ledger_for_append(db)

    last_entry_result = await db.execute(
        select(AuditLedgerEntry).order_by(AuditLedgerEntry.id.desc()).limit(1)
    )
    last_entry = last_entry_result.scalar_one_or_none()
    prev_hash = last_entry.entry_hash if last_entry else GENESIS_HASH

    occurred_at = datetime.now(timezone.utc)
    request_meta = extract_request_metadata(request)
    details_payload = jsonable_encoder(details if details is not None else {})

    payload = build_audit_hash_payload(
        occurred_at=occurred_at,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_method=request_meta["request_method"],
        request_path=request_meta["request_path"],
        ip_address=request_meta["ip_address"],
        user_agent=request_meta["user_agent"],
        details=details_payload,
    )
    entry_hash = compute_audit_entry_hash(prev_hash=prev_hash, payload=payload)

    entry = AuditLedgerEntry(
        occurred_at=occurred_at,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        request_method=request_meta["request_method"],
        request_path=request_meta["request_path"],
        ip_address=request_meta["ip_address"],
        user_agent=request_meta["user_agent"],
        details=details_payload,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    await db.flush()
    return entry


def verify_audit_chain_entries(entries: Sequence[AuditLedgerEntry]) -> AuditChainVerification:
    prev_hash = GENESIS_HASH
    checked_entries = 0
    latest_hash: str | None = None

    for entry in entries:
        checked_entries += 1
        latest_hash = entry.entry_hash

        if entry.prev_hash != prev_hash:
            return AuditChainVerification(
                is_valid=False,
                checked_entries=checked_entries,
                broken_entry_id=entry.id,
                reason="prev_hash_mismatch",
                expected_hash=prev_hash,
                actual_hash=entry.prev_hash,
                latest_hash=latest_hash,
            )

        payload = build_audit_hash_payload(
            occurred_at=entry.occurred_at,
            actor_user_id=entry.actor_user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            request_method=entry.request_method,
            request_path=entry.request_path,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            details=entry.details,
        )
        expected_hash = compute_audit_entry_hash(prev_hash=prev_hash, payload=payload)
        if entry.entry_hash != expected_hash:
            return AuditChainVerification(
                is_valid=False,
                checked_entries=checked_entries,
                broken_entry_id=entry.id,
                reason="entry_hash_mismatch",
                expected_hash=expected_hash,
                actual_hash=entry.entry_hash,
                latest_hash=latest_hash,
            )

        prev_hash = entry.entry_hash

    return AuditChainVerification(
        is_valid=True,
        checked_entries=checked_entries,
        broken_entry_id=None,
        reason=None,
        expected_hash=None,
        actual_hash=None,
        latest_hash=latest_hash,
    )


async def verify_audit_chain(db: AsyncSession) -> AuditChainVerification:
    result = await db.execute(select(AuditLedgerEntry).order_by(AuditLedgerEntry.id.asc()))
    entries = result.scalars().all()
    return verify_audit_chain_entries(entries)
