from datetime import datetime

import pytest

from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle

from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.signal_history_service import SignalHistoryService
from app.services.signal_lifecycle_coordinator import (
    SignalLifecycleCoordinator,
)


def create_registered_signal():
    registry = ActiveSignalRegistry()
    history = SignalHistoryService()

    signal = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.90,
        reason="Bullish confirmation.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )

    lifecycle = SignalLifecycle(
        signal_id="TW-001",
        status="NEW",
    )

    registry.register(signal, lifecycle)

    coordinator = SignalLifecycleCoordinator(
        registry=registry,
        history_service=history,
    )

    return registry, history, coordinator


def test_successful_transition_is_recorded():
    registry, history, coordinator = create_registered_signal()

    timestamp = datetime(2026, 11, 3, 10, 5)

    coordinator.activate(
        "TW-001",
        occurred_at=timestamp,
        reason="Confirmation completed.",
    )

    events = history.get_history("TW-001")

    assert len(events) == 1
    assert events[0].previous_status == "NEW"
    assert events[0].new_status == "ACTIVE"
    assert events[0].occurred_at == timestamp
    assert events[0].reason == "Confirmation completed."


def test_invalid_transition_is_not_recorded():
    registry, history, coordinator = create_registered_signal()

    with pytest.raises(ValueError):
        coordinator.expire("TW-001")

    assert history.count("TW-001") == 0

    lifecycle = registry.get_lifecycle("TW-001")

    assert lifecycle is not None
    assert lifecycle.status == "NEW"


def test_unknown_signal_does_not_create_history():
    _, history, coordinator = create_registered_signal()

    with pytest.raises(ValueError):
        coordinator.activate("UNKNOWN")

    assert history.count("UNKNOWN") == 0


def test_multiple_transitions_are_recorded_in_order():
    _, history, coordinator = create_registered_signal()

    coordinator.activate(
        "TW-001",
        occurred_at=datetime(2026, 11, 3, 10, 5),
    )

    coordinator.mark_updated(
        "TW-001",
        occurred_at=datetime(2026, 11, 3, 10, 10),
        reason="Signal parameters updated.",
    )

    coordinator.expire(
        "TW-001",
        occurred_at=datetime(2026, 11, 3, 10, 15),
        reason="Signal expired.",
    )

    events = history.get_history("TW-001")

    assert len(events) == 3

    assert [
        (event.previous_status, event.new_status)
        for event in events
    ] == [
        ("NEW", "ACTIVE"),
        ("ACTIVE", "UPDATED"),
        ("UPDATED", "EXPIRED"),
    ]

def test_new_signal_registration_is_recorded():
    registry = ActiveSignalRegistry()
    history = SignalHistoryService()

    coordinator = SignalLifecycleCoordinator(
        registry=registry,
        history_service=history,
    )

    signal = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.90,
        reason="Bullish confirmation.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )

    lifecycle = SignalLifecycle(
        signal_id="TW-002",
        status="NEW",
    )

    coordinator.register_signal(
        signal=signal,
        lifecycle=lifecycle,
        occurred_at=signal.detected_at,
        reason="New trading signal generated.",
    )

    events = history.get_history("TW-002")

    assert len(events) == 1
    assert events[0].previous_status is None
    assert events[0].new_status == "NEW"
    assert events[0].reason == "New trading signal generated."


def test_registration_rejects_non_new_lifecycle():
    registry = ActiveSignalRegistry()
    history = SignalHistoryService()

    coordinator = SignalLifecycleCoordinator(
        registry=registry,
        history_service=history,
    )

    signal = SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.90,
        reason="Bullish confirmation.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )

    lifecycle = SignalLifecycle(
        signal_id="TW-003",
        status="ACTIVE",
    )

    with pytest.raises(ValueError):
        coordinator.register_signal(
            signal=signal,
            lifecycle=lifecycle,
        )

    assert registry.get("TW-003") is None
    assert history.count("TW-003") == 0