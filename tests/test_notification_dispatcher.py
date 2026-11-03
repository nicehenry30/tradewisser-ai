from datetime import datetime

from app.models.signal_notification import SignalNotification
from app.services.notification_channel import NotificationChannel
from app.services.notification_dispatcher import (
    NotificationDispatcher,
)


class FakeChannel(NotificationChannel):
    def __init__(
        self,
        channel_name: str,
        should_succeed: bool = True,
        should_raise: bool = False,
    ):
        self._name = channel_name
        self._should_succeed = should_succeed
        self._should_raise = should_raise
        self.sent_notifications = []

    @property
    def name(self) -> str:
        return self._name

    def send(
        self,
        notification: SignalNotification,
    ) -> bool:
        if self._should_raise:
            raise RuntimeError(
                f"{self._name} delivery failed"
            )

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


def test_dispatcher_sends_to_all_channels():
    notification = make_notification()

    flutter = FakeChannel("flutter")
    telegram = FakeChannel("telegram")
    email = FakeChannel("email")

    dispatcher = NotificationDispatcher(
        channels=[
            flutter,
            telegram,
            email,
        ]
    )

    result = dispatcher.dispatch(notification)

    assert result.delivered is True

    assert result.successful_channels == (
        "flutter",
        "telegram",
        "email",
    )

    assert result.failed_channels == ()

    assert flutter.sent_notifications == [notification]
    assert telegram.sent_notifications == [notification]
    assert email.sent_notifications == [notification]


def test_failed_channel_does_not_stop_other_channels():
    notification = make_notification()

    flutter = FakeChannel("flutter")
    telegram = FakeChannel(
        "telegram",
        should_succeed=False,
    )
    email = FakeChannel("email")

    dispatcher = NotificationDispatcher(
        channels=[
            flutter,
            telegram,
            email,
        ]
    )

    result = dispatcher.dispatch(notification)

    assert result.delivered is True

    assert result.successful_channels == (
        "flutter",
        "email",
    )

    assert result.failed_channels == (
        "telegram",
    )

    assert flutter.sent_notifications == [notification]
    assert telegram.sent_notifications == [notification]
    assert email.sent_notifications == [notification]


def test_channel_exception_does_not_break_dispatch():
    notification = make_notification()

    broken_channel = FakeChannel(
        "telegram",
        should_raise=True,
    )

    working_channel = FakeChannel("flutter")

    dispatcher = NotificationDispatcher(
        channels=[
            broken_channel,
            working_channel,
        ]
    )

    result = dispatcher.dispatch(notification)

    assert result.delivered is True

    assert result.successful_channels == (
        "flutter",
    )

    assert result.failed_channels == (
        "telegram",
    )

    assert working_channel.sent_notifications == [notification]


def test_dispatcher_reports_no_delivery_when_all_channels_fail():
    notification = make_notification()

    telegram = FakeChannel(
        "telegram",
        should_succeed=False,
    )

    email = FakeChannel(
        "email",
        should_raise=True,
    )

    dispatcher = NotificationDispatcher(
        channels=[
            telegram,
            email,
        ]
    )

    result = dispatcher.dispatch(notification)

    assert result.delivered is False

    assert result.successful_channels == ()

    assert result.failed_channels == (
        "telegram",
        "email",
    )


def test_dispatcher_with_no_channels():
    notification = make_notification()

    dispatcher = NotificationDispatcher()

    result = dispatcher.dispatch(notification)

    assert result.delivered is False
    assert result.successful_channels == ()
    assert result.failed_channels == ()
    assert result.signal_id == "XAUUSD-BUY-001"