from app.services.risk_management_service import (
    RiskManagementService,
)


class StubRiskPolicy:
    def __init__(self):
        self.calls = []

    def validate(
        self,
        account_balance,
        risk_percent,
    ):
        self.calls.append(
            (
                account_balance,
                risk_percent,
            )
        )


class StubRiskCalculator:
    def __init__(self):
        self.calls = []

    def calculate_risk_amount(
        self,
        account_balance,
        risk_percent,
    ):
        self.calls.append(
            (
                account_balance,
                risk_percent,
            )
        )
        return 100.0


class StubInstrumentService:
    def __init__(self):
        self.calls = []

    def get_instrument(self, symbol):
        self.calls.append(symbol)
        return "INSTRUMENT"


class StubPositionSizeCalculator:
    def __init__(self):
        self.calls = []

    def calculate_position_size(
        self,
        risk_amount,
        entry_price,
        stop_loss_price,
        instrument,
    ):
        self.calls.append(
            (
                risk_amount,
                entry_price,
                stop_loss_price,
                instrument,
            )
        )
        return 0.5


def build_service():
    risk_policy = StubRiskPolicy()
    risk_calculator = StubRiskCalculator()
    instrument_service = StubInstrumentService()
    position_size_calculator = StubPositionSizeCalculator()

    service = RiskManagementService(
        risk_policy=risk_policy,
        risk_calculator=risk_calculator,
        instrument_service=instrument_service,
        position_size_calculator=position_size_calculator,
    )

    return (
        service,
        risk_policy,
        risk_calculator,
        instrument_service,
        position_size_calculator,
    )


def test_risk_management_calculates_risk_and_position_size():
    (
        service,
        risk_policy,
        risk_calculator,
        instrument_service,
        position_size_calculator,
    ) = build_service()

    result = service.calculate(
        symbol="XAUUSD",
        account_balance=10_000.0,
        risk_percent=1.0,
        entry_price=100.0,
        stop_loss_price=98.0,
    )

    assert result["risk_amount"] == 100.0
    assert result["position_size"] == 0.5

    assert risk_policy.calls == [
        (10_000.0, 1.0)
    ]

    assert risk_calculator.calls == [
        (10_000.0, 1.0)
    ]

    assert instrument_service.calls == [
        "XAUUSD"
    ]

    assert position_size_calculator.calls == [
        (
            100.0,
            100.0,
            98.0,
            "INSTRUMENT",
        )
    ]

def test_risk_policy_rejection_stops_position_size_calculation():
    (
        service,
        risk_policy,
        risk_calculator,
        instrument_service,
        position_size_calculator,
    ) = build_service()

    def reject_risk(
        account_balance,
        risk_percent,
    ):
        raise ValueError(
            "Requested risk exceeds policy."
        )

    risk_policy.validate = reject_risk

    import pytest

    with pytest.raises(
        ValueError,
        match="Requested risk exceeds policy",
    ):
        service.calculate(
            symbol="XAUUSD",
            account_balance=10_000.0,
            risk_percent=3.0,
            entry_price=100.0,
            stop_loss_price=98.0,
        )

    assert risk_calculator.calls == []
    assert instrument_service.calls == []
    assert position_size_calculator.calls == []