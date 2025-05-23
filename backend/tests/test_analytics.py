## backend/tests/test_analytics.py

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models.estimate import Estimate, EstimateStatus
from app.models.item import EstimateItem

from datetime import datetime


@pytest.mark.asyncio
async def test_global_analytics_empty(client: AsyncClient):
    # без одной записи в БД ожидаем 404
    resp = await client.get("/api/analytics/")
    assert resp.status_code == 404


@pytest_asyncio.fixture
async def seed_estimates(db_session):
    # две сметы в двух разных месяцах
    est1 = Estimate(
        name="A",
        date=datetime(2025, 5, 2, 10, 0, 0),
        client_id=1,
        user_id=1,
        status=EstimateStatus.PAID,
        vat_enabled=True,
    )
    est1.items = [EstimateItem(name="X", quantity=1, unit_price=100)]
    est2 = Estimate(
        name="B",
        date=datetime(2025, 4, 1, 10, 0, 0),
        client_id=1,
        user_id=1,
        status=EstimateStatus.PAID,
        vat_enabled=True,
    )
    est2.items = [EstimateItem(name="Y", quantity=2, unit_price=50)]
    db_session.add_all([est1, est2])
    await db_session.commit()
    yield


@pytest.mark.asyncio
async def test_global_analytics_two_periods(client: AsyncClient, seed_estimates):
    resp = await client.get("/api/analytics/?granularity=month")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_estimates"] == 2
    periods = [p["period"] for p in data["timeseries"]]
    assert set(periods) == {"2025-04", "2025-05"}
    assert data["mom_growth"] is not None
