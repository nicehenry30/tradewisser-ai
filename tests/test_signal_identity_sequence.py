from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.signal_identity_service import SignalIdentityService


def make_signal(
    symbol="XAUUSD",
    direction="BUY",
):
    return SignalEvent(
        symbol=symbol,
        direction=direction,
        status="SIGNAL",
        confidence=0.85,
        reason="Bullish opportunity detected.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )


def test_first_opportunity_gets_sequence_one():
    service = SignalIdentityService()

    signal_id = service.create_new_id(
        make_signal()
    )

    assert signal_id == "XAUUSD-BUY-001"


def test_second_new_opportunity_gets_sequence_two():
    service = SignalIdentityService()

    first_id = service.create_new_id(
        make_signal()
    )

    second_id = service.create_new_id(
        make_signal()
    )

    assert first_id == "XAUUSD-BUY-001"
    assert second_id == "XAUUSD-BUY-002"


def test_different_direction_has_separate_sequence():
    service = SignalIdentityService()

    buy_id = service.create_new_id(
        make_signal(direction="BUY")
    )

    sell_id = service.create_new_id(
        make_signal(direction="SELL")
    )

    assert buy_id == "XAUUSD-BUY-001"
    assert sell_id == "XAUUSD-SELL-001"


def test_different_symbol_has_separate_sequence():
    service = SignalIdentityService()

    xauusd_id = service.create_new_id(
        make_signal(symbol="XAUUSD")
    )

    eurusd_id = service.create_new_id(
        make_signal(symbol="EURUSD")
    )

    assert xauusd_id == "XAUUSD-BUY-001"
    assert eurusd_id == "EURUSD-BUY-001"


def test_sequence_is_independent_of_signal_reason():
    service = SignalIdentityService()

    first = make_signal()

    second = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.95,
        reason="Completely different analysis wording.",
        detected_at=datetime(2026, 11, 3, 10, 5),
    )

    assert service.create_new_id(first) == "XAUUSD-BUY-001"
    assert service.create_new_id(second) == "XAUUSD-BUY-002"
