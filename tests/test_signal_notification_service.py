from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.notification_channel import NotificationChannel
from app.services.notification_dispatcher import (
    NotificationDispatcher,
)
from app.services.signal_notification_service import (
    SignalNotificationService,
)


class FakeChannel(NotificationChannel):
    def __init__(self):
        self.sent_notifications = []

    @property
    def name(self) -> str:
        return "fake"

    def send(self, notification):
        self.sent_notifications.append(notification)
        return True


def make_signal(
    status: str = "DEVELOPING",
    direction: str = "BUY",
    confidence: float = 0.78,
    reason: str = "Quantitative evidence is improving.",
):
    return SignalEvent(
        symbol="XAUUSD",
        direction=direction,
        status=status,
        confidence=confidence,
        reason=reason,
        detected_at=datetime(
            2026,
            11,
            3,
            12,
            0,
        ),
    )


def make_service():
    channel = FakeChannel()

    dispatcher = NotificationDispatcher(
        channels=[channel]
    )

    service = SignalNotificationService(
        dispatcher=dispatcher
    )

    return service, channel


def test_developing_signal_creates_notification():
    service, channel = make_service()

    signal = make_signal(
        status="DEVELOPING"
    )

    notification = service.notify(signal)

    assert notification is not None
    assert notification.symbol == "XAUUSD"
    assert notification.direction == "BUY"
    assert notification.status == "DEVELOPING"
    assert notification.confidence == 0.78

    assert len(channel.sent_notifications) == 1


def test_signal_creates_notification():
    service, channel = make_service()

    signal = make_signal(
        status="SIGNAL"
    )

    notification = service.notify(signal)

    assert notification is not None
    assert notification.status == "SIGNAL"
    assert "signal detected" in notification.title.lower()

    assert len(channel.sent_notifications) == 1


def test_wait_signal_does_not_create_notification():
    service, channel = make_service()

    signal = make_signal(
        status="WAIT"
    )

    notification = service.notify(signal)

    assert notification is None
    assert channel.sent_notifications == []


def test_duplicate_signal_is_suppressed():
    service, channel = make_service()

    signal = make_signal(
        status="DEVELOPING"
    )

    first = service.notify(signal)
    second = service.notify(signal)

    assert first is not None
    assert second is None

    assert len(channel.sent_notifications) == 1


def test_status_change_creates_new_notification():
    service, channel = make_service()

    developing = make_signal(
        status="DEVELOPING"
    )

    actionable = make_signal(
        status="SIGNAL"
    )

    first = service.notify(developing)
    second = service.notify(actionable)

    assert first is not None
    assert second is not None

    assert len(channel.sent_notifications) == 2


def test_notification_contains_reason_and_confidence():
    service, _ = make_service()

    signal = make_signal(
        status="DEVELOPING",
        confidence=0.91,
        reason="Trend and quantitative evidence are aligned.",
    )

    notification = service.notify(signal)

    assert notification is not None
    assert "91%" in notification.message
    assert (
        "Trend and quantitative evidence are aligned."
        in notification.message
    )


def test_notify_with_result_returns_delivery_result():
    service, channel = make_service()

    signal = make_signal(
        status="SIGNAL"
    )

    notification, result = service.notify_with_result(
        signal
    )

    assert notification is not None
    assert result is not None

    assert result.delivered is True
    assert result.successful_channels == ("fake",)
    assert result.failed_channels == ()

    assert len(channel.sent_notifications) == 1


def test_duplicate_notify_with_result_is_suppressed():
    service, channel = make_service()

    signal = make_signal(
        status="SIGNAL"
    )

    first_notification, first_result = (
        service.notify_with_result(signal)
    )

    second_notification, second_result = (
        service.notify_with_result(signal)
    )

    assert first_notification is not None
    assert first_result is not None

    assert second_notification is None
    assert second_result is None

    assert len(channel.sent_notifications) == 1