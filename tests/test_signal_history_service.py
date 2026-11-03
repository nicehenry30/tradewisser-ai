from datetime import datetime

from app.models.signal_transition_event import (
    SignalTransitionEvent,
)

from app.services.signal_history_service import (
    SignalHistoryService,
)


def create_event(
    signal_id: str,
    previous_status: str | None,
    new_status: str,
    minute: int,
) -> SignalTransitionEvent:
    return SignalTransitionEvent(
        signal_id=signal_id,
        previous_status=previous_status,
        new_status=new_status,
        occurred_at=datetime(
            2026, 11, 3, 10, minute
        ),
    )


def test_history_service_records_event():
    service = SignalHistoryService()

    event = create_event(
        "TW-001",
        "NEW",
        "ACTIVE",
        0,
    )

    service.record(event)

    assert service.count("TW-001") == 1


def test_history_service_retrieves_signal_history():
    service = SignalHistoryService()

    first_event = create_event(
        "TW-001",
        None,
        "NEW",
        0,
    )

    second_event = create_event(
        "TW-001",
        "NEW",
        "ACTIVE",
        5,
    )

    service.record(first_event)
    service.record(second_event)

    history = service.get_history("TW-001")

    assert len(history) == 2
    assert history[0].new_status == "NEW"
    assert history[1].new_status == "ACTIVE"


def test_history_is_separated_by_signal_id():
    service = SignalHistoryService()

    service.record(
        create_event("TW-001", None, "NEW", 0)
    )

    service.record(
        create_event("TW-002", None, "NEW", 1)
    )

    assert service.count("TW-001") == 1
    assert service.count("TW-002") == 1


def test_unknown_signal_returns_empty_history():
    service = SignalHistoryService()

    assert service.get_history("UNKNOWN") == []


def test_history_service_returns_latest_event():
    service = SignalHistoryService()

    service.record(
        create_event("TW-001", None, "NEW", 0)
    )

    service.record(
        create_event("TW-001", "NEW", "ACTIVE", 5)
    )

    latest = service.get_latest("TW-001")

    assert latest is not None
    assert latest.new_status == "ACTIVE"


def test_latest_event_returns_none_for_unknown_signal():
    service = SignalHistoryService()

    assert service.get_latest("UNKNOWN") is None


def test_history_count_returns_correct_number():
    service = SignalHistoryService()

    service.record(
        create_event("TW-001", None, "NEW", 0)
    )

    service.record(
        create_event("TW-001", "NEW", "ACTIVE", 5)
    )

    service.record(
        create_event("TW-001", "ACTIVE", "UPDATED", 10)
    )

    assert service.count("TW-001") == 3


def test_list_signal_ids_returns_registered_ids():
    service = SignalHistoryService()

    service.record(
        create_event("TW-002", None, "NEW", 0)
    )

    service.record(
        create_event("TW-001", None, "NEW", 1)
    )

    assert service.list_signal_ids() == [
        "TW-001",
        "TW-002",
    ]


def test_history_returns_copy_not_internal_list():
    service = SignalHistoryService()

    service.record(
        create_event("TW-001", None, "NEW", 0)
    )

    history = service.get_history("TW-001")
    history.clear()

    assert service.count("TW-001") == 1