from datetime import datetime

import pytest

from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.active_signal_registry import ActiveSignalRegistry


def make_signal():
    return SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.85,
        reason="Bullish opportunity detected.",
        detected_at=datetime(2026, 11, 3, 10, 0),
    )


def make_lifecycle(status="NEW"):
    return SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status=status,
    )


def test_lifecycle_can_be_updated():
    registry = ActiveSignalRegistry()

    registry.register(
        make_signal(),
        make_lifecycle("NEW"),
    )

    updated = registry.update_lifecycle(
        "XAUUSD-BUY-001",
        "ACTIVE",
    )

    assert updated.status == "ACTIVE"


def test_updated_lifecycle_is_stored():
    registry = ActiveSignalRegistry()

    registry.register(
        make_signal(),
        make_lifecycle("NEW"),
    )

    registry.update_lifecycle(
        "XAUUSD-BUY-001",
        "ACTIVE",
    )

    assert (
        registry.get_active("XAUUSD-BUY-001")
        is not None
    )


def test_active_signal_can_be_expired():
    registry = ActiveSignalRegistry()

    registry.register(
        make_signal(),
        make_lifecycle("NEW"),
    )

    registry.update_lifecycle(
        "XAUUSD-BUY-001",
        "ACTIVE",
    )

    updated = registry.update_lifecycle(
        "XAUUSD-BUY-001",
        "EXPIRED",
    )

    assert updated.status == "EXPIRED"

    assert (
        registry.get_active("XAUUSD-BUY-001")
        is None
    )


def test_invalid_lifecycle_transition_is_rejected():
    registry = ActiveSignalRegistry()

    registry.register(
        make_signal(),
        make_lifecycle("NEW"),
    )

    with pytest.raises(ValueError):
        registry.update_lifecycle(
            "XAUUSD-BUY-001",
            "EXPIRED",
        )


def test_unknown_signal_cannot_update_lifecycle():
    registry = ActiveSignalRegistry()

    with pytest.raises(ValueError):
        registry.update_lifecycle(
            "UNKNOWN-001",
            "ACTIVE",
        )
