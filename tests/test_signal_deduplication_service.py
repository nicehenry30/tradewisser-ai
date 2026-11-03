from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.signal_deduplication_service import SignalDeduplicationService


def make_signal(
    symbol="XAUUSD",
    direction="BUY",
    status="SIGNAL",
    confidence=0.85,
    reason="Bullish opportunity detected.",
):
    return SignalEvent(
        symbol=symbol,
        direction=direction,
        status=status,
        confidence=confidence,
        reason=reason,
        detected_at=datetime(2026, 11, 3, 10, 0),
    )


def test_first_signal_is_not_duplicate():
    service = SignalDeduplicationService()

    signal = make_signal()

    assert service.is_duplicate(signal) is False


def test_same_signal_is_duplicate():
    service = SignalDeduplicationService()

    signal = make_signal()

    service.register(signal)

    assert service.is_duplicate(signal) is True


def test_different_direction_is_not_duplicate():
    service = SignalDeduplicationService()

    buy_signal = make_signal(direction="BUY")
    sell_signal = make_signal(direction="SELL")

    service.register(buy_signal)

    assert service.is_duplicate(sell_signal) is False


def test_different_symbol_is_not_duplicate():
    service = SignalDeduplicationService()

    xauusd_signal = make_signal(symbol="XAUUSD")
    eurusd_signal = make_signal(symbol="EURUSD")

    service.register(xauusd_signal)

    assert service.is_duplicate(eurusd_signal) is False


def test_different_status_is_not_duplicate():
    service = SignalDeduplicationService()

    signal = make_signal(status="SIGNAL")
    developing_signal = make_signal(status="DEVELOPING")

    service.register(signal)

    assert service.is_duplicate(developing_signal) is False


def test_registering_signal_makes_it_duplicate():
    service = SignalDeduplicationService()

    signal = make_signal()

    assert service.is_duplicate(signal) is False

    service.register(signal)

    assert service.is_duplicate(signal) is True


def test_clear_removes_signal_from_deduplication():
    service = SignalDeduplicationService()

    signal = make_signal()

    service.register(signal)

    assert service.is_duplicate(signal) is True

    service.clear(signal)

    assert service.is_duplicate(signal) is False
