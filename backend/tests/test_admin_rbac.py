from contextlib import contextmanager
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.utils.auth import get_current_user


class _ScalarResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class _MockDb:
    async def scalar(self, *_args, **_kwargs):
        return 1

    async def execute(self, *_args, **_kwargs):
        return _ScalarResult(
            [
                SimpleNamespace(
                    id=1,
                    email="admin@example.com",
                    login="admin",
                    name="Админ",
                    company=None,
                    is_admin=True,
                    is_active=True,
                )
            ]
        )


@contextmanager
def _client_with(user):
    async def _override_get_current_user():
        return user

    async def _override_get_db():
        yield _MockDb()

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_admin_users_route_denies_non_admin_user():
    with _client_with(SimpleNamespace(id=2, is_admin=False, is_active=True)) as client:
        response = client.get("/api/admin/users")

    assert response.status_code == 403


def test_admin_users_route_allows_admin_user():
    with _client_with(SimpleNamespace(id=1, is_admin=True, is_active=True)) as client:
        response = client.get("/api/admin/users?page=1&limit=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["is_admin"] is True


def test_admin_role_update_self_demote_is_blocked():
    async def _override_get_current_user():
        return SimpleNamespace(id=1, is_admin=True, is_active=True)

    async def _override_get_db():
        class _Db:
            async def execute(self, *_args, **_kwargs):
                return _ScalarResult(
                    [
                        SimpleNamespace(
                            id=1,
                            email="admin@example.com",
                            login="admin",
                            name="Админ",
                            company=None,
                            is_admin=True,
                            is_active=True,
                        )
                    ]
                )

            async def commit(self):
                return None

            async def refresh(self, _obj):
                return None

        yield _Db()

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(app) as client:
            response = client.patch("/api/admin/users/1/role", json={"is_admin": False})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
