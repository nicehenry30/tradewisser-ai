from datetime import datetime

from app.models.signal_event import SignalEvent
from app.services.notification_policy import NotificationPolicy


def make_signal(status: str) -> SignalEvent:
    return SignalEvent(
        symbol="XAUUSD",
        direction="BUY",
        status=status,
        confidence=0.78,
        reason="Higher-timeframe structure is developing.",
        detected_at=datetime.now(),
    )


def test_developing_signal_should_notify():
    policy = NotificationPolicy()

    assert policy.should_notify(
        make_signal("DEVELOPING")
    ) is True


def test_signal_should_notify():
    policy = NotificationPolicy()

    assert policy.should_notify(
        make_signal("SIGNAL")
    ) is True


def test_authorized_signal_should_notify():
    policy = NotificationPolicy()

    assert policy.should_notify(
        make_signal("AUTHORIZED")
    ) is True


def test_wait_should_not_notify():
    policy = NotificationPolicy()

    assert policy.should_notify(
        make_signal("WAIT")
    ) is False


def test_potential_should_not_notify():
    policy = NotificationPolicy()

    assert policy.should_notify(
        make_signal("POTENTIAL")
    ) is False