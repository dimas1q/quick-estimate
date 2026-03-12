from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.estimates import (
    build_financial_document_number,
    calculate_estimate_totals,
    ensure_financial_documents_allowed,
)
from app.models.estimate import EstimateStatus


def test_financial_documents_allowed_for_approved_and_paid_statuses():
    approved = SimpleNamespace(status=EstimateStatus.APPROVED)
    paid = SimpleNamespace(status=EstimateStatus.PAID)

    ensure_financial_documents_allowed(approved)
    ensure_financial_documents_allowed(paid)


def test_financial_documents_rejected_for_non_final_status():
    draft = SimpleNamespace(status=EstimateStatus.DRAFT)

    with pytest.raises(HTTPException) as error:
        ensure_financial_documents_allowed(draft)

    assert error.value.status_code == 409


def test_calculate_estimate_totals_with_internal_prices_and_vat():
    estimate = SimpleNamespace(
        use_internal_price=True,
        vat_enabled=True,
        vat_rate=20,
        items=[
            SimpleNamespace(quantity=2, internal_price=100, external_price=150),
            SimpleNamespace(quantity=1, internal_price=50, external_price=80),
        ],
    )

    totals = calculate_estimate_totals(estimate)

    assert totals["total_internal"] == 250
    assert totals["total_external"] == 380
    assert totals["total_diff"] == 130
    assert totals["vat"] == 76
    assert totals["total_with_vat"] == 456


def test_build_financial_document_number():
    issued_at = datetime(2026, 3, 13, tzinfo=timezone.utc)

    number = build_financial_document_number("INV", 42, issued_at)

    assert number == "INV-20260313-000042"
