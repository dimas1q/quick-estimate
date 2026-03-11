from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.templates import _build_import_preview


@pytest.mark.asyncio
async def test_template_import_preview_valid_payload_returns_summary_and_warnings():
    db = SimpleNamespace(scalar=AsyncMock(return_value=0))
    user = SimpleNamespace(id=10)

    payload = {
        "id": 999,
        "name": "Шаблон сцены",
        "description": "Импортируемый шаблон",
        "use_internal_price": True,
        "items": [
            {
                "id": 1,
                "name": "Свет",
                "description": "Приборы",
                "quantity": 2,
                "unit": "шт",
                "internal_price": 1000,
                "external_price": 1500,
                "category_input": "Свет",
            }
        ],
    }

    preview = await _build_import_preview(payload, db, user)

    assert preview.valid is True
    assert preview.errors == []
    assert preview.preview is not None
    assert preview.preview.items[0].category == "Свет"
    assert preview.summary is not None
    assert preview.summary.item_count == 1
    assert preview.summary.category_count == 1
    assert preview.summary.categories == ["Свет"]
    assert any("id" in warning for warning in preview.warnings)
    db.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_template_import_preview_returns_detailed_validation_errors():
    db = SimpleNamespace(scalar=AsyncMock(return_value=0))
    user = SimpleNamespace(id=10)

    payload = {
        "name": "",
        "items": [
            {
                "name": "",
                "quantity": 0,
                "unit": "невалидная",
                "internal_price": -1,
                "external_price": 0,
            }
        ],
    }

    preview = await _build_import_preview(payload, db, user)

    assert preview.valid is False
    assert preview.errors
    paths = {error.path for error in preview.errors}
    assert "name" in paths
    assert "items[0].unit" in paths
    assert any(path.startswith("items[0].") for path in paths)
    db.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_template_import_preview_warns_when_name_exists():
    db = SimpleNamespace(scalar=AsyncMock(return_value=1))
    user = SimpleNamespace(id=5)

    payload = {
        "name": "Дубликат",
        "items": [
            {
                "name": "Позиция",
                "quantity": 1,
                "unit": "шт",
                "internal_price": 100,
                "external_price": 120,
            }
        ],
    }

    preview = await _build_import_preview(payload, db, user)

    assert preview.valid is True
    assert preview.summary is not None
    assert preview.summary.name_exists is True
    assert any("уже существует" in warning for warning in preview.warnings)


@pytest.mark.asyncio
async def test_template_import_preview_rejects_non_object_payload():
    db = SimpleNamespace(scalar=AsyncMock(return_value=0))
    user = SimpleNamespace(id=1)

    preview = await _build_import_preview([1, 2, 3], db, user)

    assert preview.valid is False
    assert preview.errors[0].path == "payload"
    db.scalar.assert_not_awaited()
