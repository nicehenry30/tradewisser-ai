import pytest

from app.models.signal_lifecycle import SignalLifecycle


def test_signal_lifecycle_can_be_created():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="NEW",
    )

    assert lifecycle.signal_id == "XAUUSD-BUY-001"
    assert lifecycle.status == "NEW"


def test_signal_lifecycle_normalizes_values():
    lifecycle = SignalLifecycle(
        signal_id=" xauusd-buy-001 ",
        status=" active ",
    )

    assert lifecycle.signal_id == "XAUUSD-BUY-001"
    assert lifecycle.status == "ACTIVE"


def test_signal_lifecycle_accepts_updated_status():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="UPDATED",
    )

    assert lifecycle.status == "UPDATED"


def test_signal_lifecycle_accepts_expired_status():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="EXPIRED",
    )

    assert lifecycle.status == "EXPIRED"


def test_signal_lifecycle_rejects_empty_signal_id():
    with pytest.raises(ValueError):
        SignalLifecycle(
            signal_id="",
            status="NEW",
        )


def test_signal_lifecycle_rejects_invalid_status():
    with pytest.raises(ValueError):
        SignalLifecycle(
            signal_id="XAUUSD-BUY-001",
            status="UNKNOWN",
        )


def test_signal_lifecycle_is_immutable():
    lifecycle = SignalLifecycle(
        signal_id="XAUUSD-BUY-001",
        status="NEW",
    )

    with pytest.raises(AttributeError):
        lifecycle.status = "ACTIVE"
