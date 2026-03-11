from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.estimates import ensure_client_belongs_to_user
from app.utils.auth import get_current_admin


@pytest.mark.asyncio
async def test_ensure_client_belongs_to_user_returns_none_for_empty_client():
    db = SimpleNamespace(get=AsyncMock())
    result = await ensure_client_belongs_to_user(db, None, 10)
    assert result is None
    db.get.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_client_belongs_to_user_raises_404_when_not_found():
    db = SimpleNamespace(get=AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc_info:
        await ensure_client_belongs_to_user(db, 100, 10)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Клиент не найден"


@pytest.mark.asyncio
async def test_ensure_client_belongs_to_user_raises_403_for_foreign_client():
    foreign_client = SimpleNamespace(user_id=99)
    db = SimpleNamespace(get=AsyncMock(return_value=foreign_client))
    with pytest.raises(HTTPException) as exc_info:
        await ensure_client_belongs_to_user(db, 100, 10)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Нет доступа к этому клиенту"


@pytest.mark.asyncio
async def test_get_current_admin_denies_non_admin():
    user = SimpleNamespace(is_admin=False)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin(user)
    assert exc_info.value.status_code == 403
