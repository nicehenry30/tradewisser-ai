from datetime import datetime, timezone

import pytest

from app.models.signal_event import SignalEvent


def test_signal_event_can_be_created():
    event = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.85,
        reason="5M confirmation aligned with the 15M setup.",
        detected_at=datetime.now(timezone.utc),
    )

    assert event.symbol == "XAUUSD"
    assert event.direction == "BUY"
    assert event.status == "SIGNAL"
    assert event.confidence == 0.85
    assert event.reason == "5M confirmation aligned with the 15M setup."


def test_signal_event_normalizes_symbol_and_direction():
    event = SignalEvent(
        symbol=" xauusd ",
        direction=" buy ",
        status="signal",
        confidence=0.8,
        reason="Valid setup.",
        detected_at=datetime.now(timezone.utc),
    )

    assert event.symbol == "XAUUSD"
    assert event.direction == "BUY"
    assert event.status == "SIGNAL"


def test_signal_event_accepts_developing_status():
    event = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="DEVELOPING",
        confidence=0.65,
        reason="Potential opportunity requires confirmation.",
        detected_at=datetime.now(timezone.utc),
    )

    assert event.status == "DEVELOPING"

def test_signal_event_accepts_confirmed_status():
    event = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="CONFIRMED",
        confidence=0.78,
        reason="Lower timeframe confirmation supports the developing setup.",
        detected_at=datetime.now(timezone.utc),
    )

    assert event.status == "CONFIRMED"


def test_signal_event_rejects_invalid_direction():
    with pytest.raises(ValueError):
        SignalEvent(
            symbol="XAUUSD",
            direction="SIDEWAYS",
            status="SIGNAL",
            confidence=0.8,
            reason="Invalid direction.",
            detected_at=datetime.now(timezone.utc),
        )


def test_signal_event_rejects_invalid_status():
    with pytest.raises(ValueError):
        SignalEvent(
            symbol="XAUUSD",
            direction="BUY",
            status="UNKNOWN",
            confidence=0.8,
            reason="Invalid status.",
            detected_at=datetime.now(timezone.utc),
        )


def test_signal_event_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        SignalEvent(
            symbol="XAUUSD",
            direction="BUY",
            status="SIGNAL",
            confidence=1.5,
            reason="Invalid confidence.",
            detected_at=datetime.now(timezone.utc),
        )


def test_signal_event_rejects_empty_reason():
    with pytest.raises(ValueError):
        SignalEvent(
            symbol="XAUUSD",
            direction="BUY",
            status="SIGNAL",
            confidence=0.8,
            reason="",
            detected_at=datetime.now(timezone.utc),
        )


def test_signal_event_is_immutable():
    event = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.8,
        reason="Valid setup.",
        detected_at=datetime.now(timezone.utc),
    )

    with pytest.raises(AttributeError):
        event.status = "WAIT"
