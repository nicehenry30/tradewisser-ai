from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.notification_deduplication_service import (
    NotificationDeduplicationService,
)


def make_signal(
    status: str = "DEVELOPING",
    direction: str = "BUY",
    reason: str = "Market structure is developing.",
) -> SignalEvent:
    return SignalEvent(
        symbol="XAUUSD",
        direction=direction,
        status=status,
        confidence=0.78,
        reason=reason,
        detected_at=datetime.now(),
    )


def test_new_signal_is_not_duplicate():
    service = NotificationDeduplicationService()

    signal = make_signal()

    assert service.is_duplicate(signal) is False


def test_registered_signal_is_duplicate():
    service = NotificationDeduplicationService()

    signal = make_signal()

    service.register(signal)

    assert service.is_duplicate(signal) is True


def test_reason_change_does_not_create_new_notification():
    service = NotificationDeduplicationService()

    original = make_signal(
        reason="Quantitative evidence is improving."
    )

    updated_reason = make_signal(
        reason="Higher-timeframe structure is improving."
    )

    service.register(original)

    assert service.is_duplicate(updated_reason) is True


def test_status_change_is_not_duplicate():
    service = NotificationDeduplicationService()

    developing = make_signal(
        status="DEVELOPING"
    )

    signal = make_signal(
        status="SIGNAL"
    )

    service.register(developing)

    assert service.is_duplicate(signal) is False


def test_direction_change_is_not_duplicate():
    service = NotificationDeduplicationService()

    buy = make_signal(
        direction="BUY"
    )

    sell = make_signal(
        direction="SELL"
    )

    service.register(buy)

    assert service.is_duplicate(sell) is False


def test_clear_removes_registered_state():
    service = NotificationDeduplicationService()

    signal = make_signal()

    service.register(signal)

    assert service.is_duplicate(signal) is True

    service.clear(signal)

    assert service.is_duplicate(signal) is False