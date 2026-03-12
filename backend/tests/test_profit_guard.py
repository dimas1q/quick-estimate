from app.api.estimates import _build_profit_guard_result
from app.schemas.estimate import EstimateProfitGuardCheckIn, ProfitGuardItemInput


def test_profit_guard_detects_low_margin_rows():
    payload = EstimateProfitGuardCheckIn(
        use_internal_price=True,
        items=[
            ProfitGuardItemInput(
                name="Позиция 1",
                category="Свет",
                quantity=1,
                internal_price=900,
                external_price=1000,
            ),
            ProfitGuardItemInput(
                name="Позиция 2",
                category="Звук",
                quantity=1,
                internal_price=100,
                external_price=1000,
            ),
        ],
    )

    result = _build_profit_guard_result(payload, enabled=True, threshold_percent=15)
    assert result.enabled is True
    assert result.has_risk is True
    assert result.risk_count == 1
    assert result.risks[0].name == "Позиция 1"


def test_profit_guard_handles_disabled_internal_price_mode():
    payload = EstimateProfitGuardCheckIn(
        use_internal_price=False,
        items=[ProfitGuardItemInput(name="Позиция 1", quantity=1, internal_price=100, external_price=200)],
    )

    result = _build_profit_guard_result(payload, enabled=True, threshold_percent=15)
    assert result.enabled is True
    assert result.has_risk is False
    assert result.risk_count == 0
