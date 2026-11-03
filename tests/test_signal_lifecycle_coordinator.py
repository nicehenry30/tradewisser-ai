import pytest

from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.signal_lifecycle_coordinator import (
    SignalLifecycleCoordinator,
)


def create_signal(
    signal_id: str = "SIGNAL-001",
) -> SignalEvent:
    from datetime import datetime

    return SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status="SIGNAL",
        confidence=0.90,
        reason="Test signal",
        detected_at=datetime.now(),
    )


def create_registry(
    signal_id: str = "SIGNAL-001",
    lifecycle_status: str = "NEW",
) -> ActiveSignalRegistry:
    registry = ActiveSignalRegistry()

    registry.register(
        create_signal(signal_id),
        SignalLifecycle(
            signal_id=signal_id,
            status=lifecycle_status,
        ),
    )

    return registry


def test_activate_transitions_new_signal_to_active():
    registry = create_registry()
    coordinator = SignalLifecycleCoordinator(registry)

    lifecycle = coordinator.activate("SIGNAL-001")

    assert lifecycle.status == "ACTIVE"

    stored = registry.get_lifecycle("SIGNAL-001")

    assert stored is not None
    assert stored.status == "ACTIVE"


def test_mark_updated_transitions_active_signal_to_updated():
    registry = create_registry(
        lifecycle_status="ACTIVE",
    )

    coordinator = SignalLifecycleCoordinator(registry)

    lifecycle = coordinator.mark_updated("SIGNAL-001")

    assert lifecycle.status == "UPDATED"

    stored = registry.get_lifecycle("SIGNAL-001")

    assert stored is not None
    assert stored.status == "UPDATED"


def test_expire_transitions_active_signal_to_expired():
    registry = create_registry(
        lifecycle_status="ACTIVE",
    )

    coordinator = SignalLifecycleCoordinator(registry)

    lifecycle = coordinator.expire("SIGNAL-001")

    assert lifecycle.status == "EXPIRED"

    stored = registry.get_lifecycle("SIGNAL-001")

    assert stored is not None
    assert stored.status == "EXPIRED"


def test_coordinator_rejects_invalid_transition():
    registry = create_registry(
        lifecycle_status="EXPIRED",
    )

    coordinator = SignalLifecycleCoordinator(registry)

    with pytest.raises(ValueError):
        coordinator.activate("SIGNAL-001")


def test_coordinator_rejects_unknown_signal():
    registry = ActiveSignalRegistry()

    coordinator = SignalLifecycleCoordinator(registry)

    with pytest.raises(ValueError):
        coordinator.activate("UNKNOWN")


def test_coordinator_normalizes_signal_id():
    registry = create_registry(
        signal_id="SIGNAL-001",
    )

    coordinator = SignalLifecycleCoordinator(registry)

    lifecycle = coordinator.activate(" signal-001 ")

    assert lifecycle.status == "ACTIVE"