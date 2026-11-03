from datetime import datetime

import pytest

from app.models.signal_notification import SignalNotification


def make_notification(**overrides):
    values = {
        "signal_id": "XAUUSD-BUY-001",
        "symbol": "XAUUSD",
        "direction": "BUY",
        "status": "DEVELOPING",
        "confidence": 0.78,
        "title": "XAUUSD BUY opportunity detected",
        "message": "XAUUSD is developing a potential BUY opportunity.",
        "created_at": datetime.now(),
    }

    values.update(overrides)

    return SignalNotification(**values)


def test_valid_notification():
    notification = make_notification()

    assert notification.signal_id == "XAUUSD-BUY-001"
    assert notification.symbol == "XAUUSD"
    assert notification.direction == "BUY"
    assert notification.status == "DEVELOPING"
    assert notification.confidence == 0.78


def test_notification_normalizes_values():
    notification = make_notification(
        signal_id="xauusd-buy-001",
        symbol="xauusd",
        direction="buy",
        status="developing",
    )

    assert notification.signal_id == "XAUUSD-BUY-001"
    assert notification.symbol == "XAUUSD"
    assert notification.direction == "BUY"
    assert notification.status == "DEVELOPING"


def test_empty_signal_id_is_rejected():
    with pytest.raises(ValueError):
        make_notification(signal_id="")


def test_empty_symbol_is_rejected():
    with pytest.raises(ValueError):
        make_notification(symbol="")


def test_invalid_direction_is_rejected():
    with pytest.raises(ValueError):
        make_notification(direction="INVALID")


def test_invalid_status_is_rejected():
    with pytest.raises(ValueError):
        make_notification(status="WAIT")


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError):
        make_notification(confidence=1.1)


def test_empty_title_is_rejected():
    with pytest.raises(ValueError):
        make_notification(title="")


def test_empty_message_is_rejected():
    with pytest.raises(ValueError):
        make_notification(message="")


def test_notification_is_immutable():
    notification = make_notification()

    with pytest.raises(Exception):
        notification.status = "SIGNAL"