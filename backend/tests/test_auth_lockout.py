from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.auth import (
    _clear_login_locks_if_needed,
    _lock_retry_after_seconds,
    _register_failed_login,
)
from app.core.config import settings


@pytest.mark.asyncio
async def test_register_failed_login_locks_user_at_threshold():
    user = SimpleNamespace(
        failed_login_attempts=settings.AUTH_MAX_FAILED_LOGIN_ATTEMPTS - 1,
        locked_until=None,
    )
    db = SimpleNamespace(commit=AsyncMock())
    now = datetime.now(timezone.utc)

    locked = await _register_failed_login(db, user, now)

    assert locked is True
    assert user.failed_login_attempts == 0
    assert user.locked_until is not None
    assert user.locked_until > now
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_failed_login_increments_when_below_threshold():
    user = SimpleNamespace(failed_login_attempts=1, locked_until=None)
    db = SimpleNamespace(commit=AsyncMock())
    now = datetime.now(timezone.utc)

    locked = await _register_failed_login(db, user, now)

    assert locked is False
    assert user.failed_login_attempts == 2
    assert user.locked_until is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_login_locks_resets_fields_when_present():
    user = SimpleNamespace(
        failed_login_attempts=3,
        locked_until=datetime.now(timezone.utc),
    )
    db = SimpleNamespace(commit=AsyncMock())

    await _clear_login_locks_if_needed(db, user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    db.commit.assert_awaited_once()


def test_lock_retry_after_seconds_is_positive():
    now = datetime.now(timezone.utc)
    locked_until = now.replace(microsecond=0)
    assert _lock_retry_after_seconds(locked_until, now) == 1
