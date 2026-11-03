from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.notification_channel import NotificationChannel
from app.services.notification_dispatcher import (
    NotificationDispatcher,
)
from app.services.signal_notification_service import (
    SignalNotificationService,
)


class RecordingChannel(NotificationChannel):
    def __init__(
        self,
        channel_name: str = "test",
        should_raise: bool = False,
    ):
        self._channel_name = channel_name
        self._should_raise = should_raise
        self.sent_notifications = []

    @property
    def name(self) -> str:
        return self._channel_name

    def send(self, notification):
        if self._should_raise:
            raise RuntimeError("Notification delivery failed")

        self.sent_notifications.append(notification)
        return True


def make_signal(
    status: str = "DEVELOPING",
    direction: str = "BUY",
) -> SignalEvent:
    return SignalEvent(
        symbol="XAUUSD",
        direction=direction,
        status=status,
        confidence=0.78,
        reason="Quantitative evidence supports the developing setup.",
        detected_at=datetime(2026, 11, 3, 12, 0),
    )


def make_notification_service(
    channel: RecordingChannel,
) -> SignalNotificationService:
    dispatcher = NotificationDispatcher(
        channels=[channel]
    )

    return SignalNotificationService(
        dispatcher=dispatcher
    )


def test_developing_signal_generates_notification():
    channel = RecordingChannel()

    service = make_notification_service(channel)

    notification = service.notify(
        make_signal("DEVELOPING")
    )

    assert notification is not None
    assert notification.status == "DEVELOPING"
    assert len(channel.sent_notifications) == 1


def test_actionable_signal_generates_notification():
    channel = RecordingChannel()

    service = make_notification_service(channel)

    notification = service.notify(
        make_signal("SIGNAL")
    )

    assert notification is not None
    assert notification.status == "SIGNAL"
    assert len(channel.sent_notifications) == 1


def test_wait_does_not_generate_notification():
    channel = RecordingChannel()

    service = make_notification_service(channel)

    notification = service.notify(
        make_signal("WAIT")
    )

    assert notification is None
    assert channel.sent_notifications == []


def test_repeated_signal_does_not_generate_duplicate_notifications():
    channel = RecordingChannel()

    service = make_notification_service(channel)

    signal = make_signal("DEVELOPING")

    first = service.notify(signal)
    second = service.notify(signal)

    assert first is not None
    assert second is None

    assert len(channel.sent_notifications) == 1


def test_signal_state_change_generates_new_notification():
    channel = RecordingChannel()

    service = make_notification_service(channel)

    developing = make_signal("DEVELOPING")
    actionable = make_signal("SIGNAL")

    first = service.notify(developing)
    second = service.notify(actionable)

    assert first is not None
    assert second is not None

    assert len(channel.sent_notifications) == 2


def test_notification_failure_does_not_raise_to_analysis_layer():
    channel = RecordingChannel(
        should_raise=True
    )

    service = make_notification_service(channel)

    notification = service.notify(
        make_signal("SIGNAL")
    )

    assert notification is not None