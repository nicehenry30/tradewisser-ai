from datetime import datetime

import pytest

from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.active_signal_registry import ActiveSignalRegistry


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


def make_lifecycle(
    signal_id="XAUUSD-BUY-001",
    status="ACTIVE",
):
    return SignalLifecycle(
        signal_id=signal_id,
        status=status,
    )


def test_signal_can_be_registered():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle()

    registry.register(
        signal,
        lifecycle,
    )

    assert registry.get("XAUUSD-BUY-001") == signal


def test_registered_signal_can_be_retrieved():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle()

    registry.register(signal, lifecycle)

    result = registry.get("XAUUSD-BUY-001")

    assert result is signal


def test_unknown_signal_returns_none():
    registry = ActiveSignalRegistry()

    assert registry.get("UNKNOWN-001") is None


def test_signal_can_be_removed():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle()

    registry.register(signal, lifecycle)
    registry.remove("XAUUSD-BUY-001")

    assert registry.get("XAUUSD-BUY-001") is None


def test_expired_signal_is_not_considered_active():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle(
        status="EXPIRED",
    )

    registry.register(signal, lifecycle)

    assert registry.get_active("XAUUSD-BUY-001") is None


def test_active_signal_can_be_found_by_market():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle()

    registry.register(signal, lifecycle)

    result = registry.find_active(
        symbol="XAUUSD",
        direction="BUY",
    )

    assert result is signal


def test_different_direction_is_not_returned():
    registry = ActiveSignalRegistry()

    signal = make_signal(
        direction="BUY",
    )
    lifecycle = make_lifecycle()

    registry.register(signal, lifecycle)

    result = registry.find_active(
        symbol="XAUUSD",
        direction="SELL",
    )

    assert result is None


def test_duplicate_signal_id_is_rejected():
    registry = ActiveSignalRegistry()

    signal = make_signal()
    lifecycle = make_lifecycle()

    registry.register(signal, lifecycle)

    with pytest.raises(ValueError):
        registry.register(signal, lifecycle)

def test_non_expired_signal_can_be_found_by_market():
    registry = ActiveSignalRegistry()

    signal = make_signal(
        status="DEVELOPING",
    )
    lifecycle = make_lifecycle(
        status="NEW",
    )

    registry.register(
        signal,
        lifecycle,
    )

    result = registry.find_existing(
        symbol="XAUUSD",
        direction="BUY",
    )

    assert result is signal


def test_expired_signal_is_not_found_as_existing():
    registry = ActiveSignalRegistry()

    signal = make_signal(
        status="SIGNAL",
    )
    lifecycle = make_lifecycle(
        status="EXPIRED",
    )

    registry.register(
        signal,
        lifecycle,
    )

    result = registry.find_existing(
        symbol="XAUUSD",
        direction="BUY",
    )

    assert result is None


def test_signal_event_can_be_updated():
    registry = ActiveSignalRegistry()

    developing_signal = make_signal(
        status="DEVELOPING",
    )

    lifecycle = make_lifecycle(
        status="NEW",
    )

    registry.register(
        developing_signal,
        lifecycle,
    )

    confirmed_signal = make_signal(
        status="CONFIRMED",
    )

    registry.update_signal(
        "XAUUSD-BUY-001",
        confirmed_signal,
    )

    result = registry.get(
        "XAUUSD-BUY-001",
    )

    assert result is confirmed_signal
    assert result.status == "CONFIRMED"
