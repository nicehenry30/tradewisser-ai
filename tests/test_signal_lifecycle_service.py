import pytest

from app.models.signal_lifecycle import SignalLifecycle
from app.services.signal_lifecycle_service import SignalLifecycleService


def test_new_signal_can_become_active():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="NEW",
    )

    service = SignalLifecycleService()

    updated = service.transition(
        lifecycle,
        "ACTIVE",
    )

    assert updated.status == "ACTIVE"
    assert updated.signal_id == "XAUUSD-BUY-001"


def test_active_signal_can_be_updated():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="ACTIVE",
    )

    service = SignalLifecycleService()

    updated = service.transition(
        lifecycle,
        "UPDATED",
    )

    assert updated.status == "UPDATED"


def test_active_signal_can_expire():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="ACTIVE",
    )

    service = SignalLifecycleService()

    updated = service.transition(
        lifecycle,
        "EXPIRED",
    )

    assert updated.status == "EXPIRED"


def test_expired_signal_cannot_become_active():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="EXPIRED",
    )

    service = SignalLifecycleService()

    with pytest.raises(ValueError):
        service.transition(
            lifecycle,
            "ACTIVE",
        )


def test_expired_signal_cannot_be_updated():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="EXPIRED",
    )

    service = SignalLifecycleService()

    with pytest.raises(ValueError):
        service.transition(
            lifecycle,
            "UPDATED",
        )


def test_new_signal_cannot_be_expired_directly():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="NEW",
    )

    service = SignalLifecycleService()

    with pytest.raises(ValueError):
        service.transition(
            lifecycle,
            "EXPIRED",
        )


def test_transition_preserves_signal_id():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="ACTIVE",
    )

    service = SignalLifecycleService()

    updated = service.transition(
        lifecycle,
        "EXPIRED",
    )

    assert updated.signal_id == lifecycle.signal_id
