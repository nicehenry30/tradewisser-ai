from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.signal_identity_service import SignalIdentityService


def make_signal(
    symbol="XAUUSD",
    direction="BUY",
    status="SIGNAL",
):
    return SignalEvent(
        symbol=symbol,
        direction=direction,
        status=status,
        confidence=0.85,
        reason="Bullish opportunity detected.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )


def test_signal_identity_is_created():
    service = SignalIdentityService()

    signal_id = service.create_id(make_signal())

    assert signal_id
    assert signal_id.startswith("XAUUSD-BUY-")


def test_same_signal_characteristics_create_same_identity():
    service = SignalIdentityService()

    signal = make_signal()

    first_id = service.create_id(signal)
    second_id = service.create_id(signal)

    assert first_id == second_id


def test_different_symbol_creates_different_identity():
    service = SignalIdentityService()

    xauusd = make_signal(symbol="XAUUSD")
    eurusd = make_signal(symbol="EURUSD")

    assert service.create_id(xauusd) != service.create_id(eurusd)


def test_different_direction_creates_different_identity():
    service = SignalIdentityService()

    buy_signal = make_signal(direction="BUY")
    sell_signal = make_signal(direction="SELL")

    assert service.create_id(buy_signal) != service.create_id(sell_signal)


def test_identity_is_not_based_on_reason_text():
    service = SignalIdentityService()

    first = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.80,
        reason="Bullish momentum detected.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )

    second = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.90,
        reason="Strong bullish structure detected.",
        detected_at=datetime(2026, 11, 3, 10, 5),
    )

    assert service.create_id(first) == service.create_id(second)
