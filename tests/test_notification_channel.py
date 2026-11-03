from datetime import datetime

import pytest

from app.models.signal_notification import SignalNotification
from app.services.notification_channel import NotificationChannel


class FakeNotificationChannel(NotificationChannel):
    def __init__(self, should_succeed: bool = True):
        self._should_succeed = should_succeed
        self.sent_notifications = []

    @property
    def name(self) -> str:
        return "fake"

    def send(
        self,
        notification: SignalNotification,
    ) -> bool:
        self.sent_notifications.append(notification)
        return self._should_succeed


def make_notification():
    return SignalNotification(
        signal_id="XAUUSD-BUY-001",
        symbol="XAUUSD",
        direction="BUY",
        status="DEVELOPING",
        confidence=0.78,
        title="XAUUSD BUY opportunity detected",
        message="XAUUSD is developing a potential BUY opportunity.",
        created_at=datetime.now(),
    )


def test_notification_channel_requires_name_and_send():
    channel = FakeNotificationChannel()

    assert channel.name == "fake"
    assert callable(channel.send)


def test_notification_channel_can_send_notification():
    channel = FakeNotificationChannel()
    notification = make_notification()

    result = channel.send(notification)

    assert result is True
    assert channel.sent_notifications == [notification]


def test_notification_channel_can_report_failure():
    channel = FakeNotificationChannel(should_succeed=False)
    notification = make_notification()

    result = channel.send(notification)

    assert result is False
    assert channel.sent_notifications == [notification]


def test_notification_channel_is_abstract():
    with pytest.raises(TypeError):
        NotificationChannel()