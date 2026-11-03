from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.signal_deduplication_service import SignalDeduplicationService
from app.services.signal_identity_service import SignalIdentityService
from app.services.signal_lifecycle_service import SignalLifecycleService


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


def test_new_opportunity_gets_new_signal_id():
    identity_service = SignalIdentityService()

    signal = make_signal()

    signal_id = identity_service.create_new_id(signal)

    assert signal_id == "XAUUSD-BUY-001"


def test_repeated_opportunity_is_detected_as_duplicate():
    identity_service = SignalIdentityService()
    deduplication_service = SignalDeduplicationService()

    signal = make_signal()

    signal_id = identity_service.create_new_id(signal)

    deduplication_service.register(signal)

    assert deduplication_service.is_duplicate(signal) is True
    assert signal_id == "XAUUSD-BUY-001"


def test_signal_can_move_from_new_to_active():
    lifecycle_service = SignalLifecycleService()

    from app.models.signal_lifecycle import SignalLifecycle

    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="NEW",
    )

    updated = lifecycle_service.transition(
        lifecycle,
        "ACTIVE",
    )

    assert updated.signal_id == "XAUUSD-BUY-001"
    assert updated.status == "ACTIVE"


def test_active_signal_can_expire():
    lifecycle_service = SignalLifecycleService()

    from app.models.signal_lifecycle import SignalLifecycle

    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="ACTIVE",
    )

    expired = lifecycle_service.transition(
        lifecycle,
        "EXPIRED",
    )

    assert expired.signal_id == "XAUUSD-BUY-001"
    assert expired.status == "EXPIRED"


def test_new_opportunity_after_expiry_gets_new_identity():
    identity_service = SignalIdentityService()

    first_signal = make_signal()

    first_id = identity_service.create_new_id(
        first_signal
    )

    second_id = identity_service.create_new_id(
        first_signal
    )

    assert first_id == "XAUUSD-BUY-001"
    assert second_id == "XAUUSD-BUY-002"


def test_different_direction_is_a_new_opportunity():
    identity_service = SignalIdentityService()

    buy_signal = make_signal(
        direction="BUY"
    )

    sell_signal = make_signal(
        direction="SELL"
    )

    buy_id = identity_service.create_new_id(
        buy_signal
    )

    sell_id = identity_service.create_new_id(
        sell_signal
    )

    assert buy_id == "XAUUSD-BUY-001"
    assert sell_id == "XAUUSD-SELL-001"
