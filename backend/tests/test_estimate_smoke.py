from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.estimates import ensure_estimate_not_read_only


def test_ensure_estimate_not_read_only_allows_editable_estimate():
    estimate = SimpleNamespace(read_only=False)

    # Should not raise for editable estimate
    ensure_estimate_not_read_only(estimate)


def test_ensure_estimate_not_read_only_rejects_read_only_estimate():
    estimate = SimpleNamespace(read_only=True)

    with pytest.raises(HTTPException) as exc_info:
        ensure_estimate_not_read_only(estimate)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Смета находится в режиме только чтение"
