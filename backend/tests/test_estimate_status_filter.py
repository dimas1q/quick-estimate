from types import SimpleNamespace

import pytest

from app.api.estimates import list_estimates


class _ExecResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _CaptureDb:
    def __init__(self):
        self.execute_queries = []

    async def scalar(self, _query):
        return 0

    async def execute(self, query):
        self.execute_queries.append(query)
        return _ExecResult([])


@pytest.mark.asyncio
async def test_list_estimates_adds_status_filter_when_status_passed():
    db = _CaptureDb()
    user = SimpleNamespace(id=7)

    await list_estimates(status="draft", page=1, limit=10, db=db, user=user)

    query = db.execute_queries[0]
    where_clause = str(query.whereclause)
    assert "estimates.status" in where_clause


@pytest.mark.asyncio
async def test_list_estimates_skips_status_filter_when_status_empty():
    db = _CaptureDb()
    user = SimpleNamespace(id=7)

    await list_estimates(status=None, page=1, limit=10, db=db, user=user)

    query = db.execute_queries[0]
    where_clause = str(query.whereclause)
    assert "estimates.status" not in where_clause
