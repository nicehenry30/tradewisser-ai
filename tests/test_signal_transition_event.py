from datetime import datetime

import pytest

from app.models.signal_transition_event import (
    SignalTransitionEvent,
)


def test_transition_event_can_be_created():
    event = SignalTransitionEvent(
        signal_id="tw-001",
        previous_status="NEW",
        new_status="ACTIVE",
        occurred_at=datetime(2026, 11, 3, 10, 0),
        reason="Signal confirmed.",
    )

    assert event.signal_id == "TW-001"
    assert event.previous_status == "NEW"
    assert event.new_status == "ACTIVE"
    assert event.reason == "Signal confirmed."


def test_transition_event_accepts_initial_new_status():
    event = SignalTransitionEvent(
        signal_id="tw-002",
        previous_status=None,
        new_status="NEW",
        occurred_at=datetime(2026, 11, 3, 10, 0),
    )

    assert event.previous_status is None
    assert event.new_status == "NEW"


def test_transition_event_normalizes_values():
    event = SignalTransitionEvent(
        signal_id=" tw-003 ",
        previous_status="active",
        new_status="updated",
        occurred_at=datetime(2026, 11, 3, 10, 0),
        reason="  Price level changed.  ",
    )

    assert event.signal_id == "TW-003"
    assert event.previous_status == "ACTIVE"
    assert event.new_status == "UPDATED"
    assert event.reason == "Price level changed."


def test_transition_event_rejects_empty_signal_id():
    with pytest.raises(ValueError):
        SignalTransitionEvent(
            signal_id=" ",
            previous_status="NEW",
            new_status="ACTIVE",
            occurred_at=datetime(2026, 11, 3, 10, 0),
        )


def test_transition_event_rejects_invalid_new_status():
    with pytest.raises(ValueError):
        SignalTransitionEvent(
            signal_id="TW-004",
            previous_status="NEW",
            new_status="INVALID",
            occurred_at=datetime(2026, 11, 3, 10, 0),
        )


def test_transition_event_rejects_invalid_previous_status():
    with pytest.raises(ValueError):
        SignalTransitionEvent(
            signal_id="TW-005",
            previous_status="INVALID",
            new_status="ACTIVE",
            occurred_at=datetime(2026, 11, 3, 10, 0),
        )


def test_transition_event_rejects_same_status_transition():
    with pytest.raises(ValueError):
        SignalTransitionEvent(
            signal_id="TW-006",
            previous_status="ACTIVE",
            new_status="ACTIVE",
            occurred_at=datetime(2026, 11, 3, 10, 0),
        )


def test_transition_event_is_immutable():
    event = SignalTransitionEvent(
        signal_id="TW-007",
        previous_status="NEW",
        new_status="ACTIVE",
        occurred_at=datetime(2026, 11, 3, 10, 0),
    )

    with pytest.raises(AttributeError):
        event.new_status = "EXPIRED"