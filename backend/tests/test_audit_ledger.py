from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.audit_ledger import (
    GENESIS_HASH,
    build_audit_hash_payload,
    compute_audit_entry_hash,
    verify_audit_chain_entries,
)


def _entry_from_payload(entry_id: int, prev_hash: str, payload: dict):
    entry_hash = compute_audit_entry_hash(prev_hash=prev_hash, payload=payload)
    return SimpleNamespace(
        id=entry_id,
        occurred_at=datetime.fromisoformat(payload["occurred_at"]),
        actor_user_id=payload["actor_user_id"],
        action=payload["action"],
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        request_method=payload["request_method"],
        request_path=payload["request_path"],
        ip_address=payload["ip_address"],
        user_agent=payload["user_agent"],
        details=payload["details"],
        prev_hash=prev_hash,
        entry_hash=entry_hash,
    )


def test_compute_audit_entry_hash_is_deterministic():
    occurred_at = datetime(2026, 3, 13, 1, 0, 0, tzinfo=timezone.utc)
    payload = build_audit_hash_payload(
        occurred_at=occurred_at,
        actor_user_id=7,
        action="estimate.export.pdf",
        entity_type="estimate",
        entity_id="42",
        request_method="GET",
        request_path="/api/estimates/42/export/pdf",
        ip_address="127.0.0.1",
        user_agent="pytest",
        details={"k": "v", "n": 1},
    )

    first = compute_audit_entry_hash(prev_hash=GENESIS_HASH, payload=payload)
    second = compute_audit_entry_hash(prev_hash=GENESIS_HASH, payload=payload)

    assert first == second
    assert len(first) == 64


def test_verify_audit_chain_entries_returns_valid_for_correct_chain():
    first_payload = build_audit_hash_payload(
        occurred_at=datetime(2026, 3, 13, 1, 0, 0, tzinfo=timezone.utc),
        actor_user_id=1,
        action="admin.user.role.changed",
        entity_type="user",
        entity_id="2",
        request_method="PATCH",
        request_path="/api/admin/users/2/role",
        ip_address="127.0.0.1",
        user_agent="pytest",
        details={"old": False, "new": True},
    )
    first_entry = _entry_from_payload(1, GENESIS_HASH, first_payload)

    second_payload = build_audit_hash_payload(
        occurred_at=datetime(2026, 3, 13, 1, 1, 0, tzinfo=timezone.utc),
        actor_user_id=1,
        action="estimate.read_only.changed",
        entity_type="estimate",
        entity_id="10",
        request_method="PATCH",
        request_path="/api/estimates/10/read-only",
        ip_address="127.0.0.1",
        user_agent="pytest",
        details={"read_only": True},
    )
    second_entry = _entry_from_payload(2, first_entry.entry_hash, second_payload)

    verification = verify_audit_chain_entries([first_entry, second_entry])

    assert verification.is_valid is True
    assert verification.checked_entries == 2
    assert verification.broken_entry_id is None


def test_verify_audit_chain_entries_detects_tampering():
    payload = build_audit_hash_payload(
        occurred_at=datetime(2026, 3, 13, 1, 0, 0, tzinfo=timezone.utc),
        actor_user_id=1,
        action="template.deleted",
        entity_type="template",
        entity_id="5",
        request_method="DELETE",
        request_path="/api/templates/5",
        ip_address="127.0.0.1",
        user_agent="pytest",
        details={"template_name": "A"},
    )
    entry = _entry_from_payload(1, GENESIS_HASH, payload)
    entry.details = {"template_name": "tampered"}

    verification = verify_audit_chain_entries([entry])

    assert verification.is_valid is False
    assert verification.broken_entry_id == 1
    assert verification.reason == "entry_hash_mismatch"
