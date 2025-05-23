## backend/tests/conftest.py

import os, sys, asyncio
import pytest_asyncio
import pytest

from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.api.auth import get_current_user

# В памяти SQLite для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(
    engine_test, expire_on_commit=False, class_=AsyncSession
)


# перехватываем зависимость get_db
async def _override_get_db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    # Создаём таблицы перед всеми тестами
    async def _prep():
        async with engine_test.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(_prep())
    yield
    # можно добавить очистку в конце, если нужно


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": "test@example.com",
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    # Фикстура прямого доступа к сессии для сидинга
    async with AsyncSessionLocal() as session:
        yield session
