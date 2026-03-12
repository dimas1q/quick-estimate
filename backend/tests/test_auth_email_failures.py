from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import auth as auth_api
from app.schemas.user import EmailRequest, UserCreate


class _ScalarResult:
    def __init__(self, item):
        self._item = item

    def scalar_one_or_none(self):
        return self._item


class _RegisterDb:
    def __init__(self):
        self._calls = 0
        self.added = []
        self.deleted = []
        self.commits = 0

    async def execute(self, *_args, **_kwargs):
        self._calls += 1
        return _ScalarResult(None)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def delete(self, obj):
        self.deleted.append(obj)

    async def refresh(self, _obj):
        return None


class _ResendDb:
    def __init__(self, user):
        self.user = user
        self.rollback = AsyncMock()
        self.commit = AsyncMock()

    async def execute(self, *_args, **_kwargs):
        return _ScalarResult(self.user)


@pytest.mark.asyncio
async def test_register_returns_502_when_smtp_send_fails(monkeypatch):
    db = _RegisterDb()
    monkeypatch.setattr(
        auth_api,
        "send_verification_code",
        AsyncMock(side_effect=RuntimeError("smtp unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_api.register(
            UserCreate(
                login="newuser",
                email="newuser@example.com",
                password="strong-password-123",
            ),
            db,
        )

    assert exc_info.value.status_code == 502
    assert db.commits == 2
    assert len(db.deleted) == 1


@pytest.mark.asyncio
async def test_resend_returns_502_and_rolls_back_when_smtp_send_fails(monkeypatch):
    user = SimpleNamespace(
        email="user@example.com",
        is_active=False,
        otp_sent_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        hashed_otp=None,
        otp_expires_at=None,
    )
    db = _ResendDb(user)
    monkeypatch.setattr(
        auth_api,
        "send_verification_code",
        AsyncMock(side_effect=RuntimeError("smtp unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_api.resend_code(EmailRequest(email=user.email), db)

    assert exc_info.value.status_code == 502
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
