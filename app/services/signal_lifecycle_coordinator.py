from datetime import datetime

from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.models.signal_transition_event import SignalTransitionEvent

from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.signal_lifecycle_service import SignalLifecycleService
from app.services.signal_history_service import SignalHistoryService


class SignalLifecycleCoordinator:
    """
    Coordinates signal registration, lifecycle transitions,
    and historical event recording.

    SignalLifecycleService validates transitions.
    ActiveSignalRegistry stores current lifecycle state.
    SignalHistoryService records historical events.

    This coordinator does not make trading decisions or
    authorize trade execution.
    """

    def __init__(
        self,
        registry: ActiveSignalRegistry,
        lifecycle_service: SignalLifecycleService | None = None,
        history_service: SignalHistoryService | None = None,
    ):
        self._registry = registry

        self._lifecycle_service = (
            lifecycle_service or SignalLifecycleService()
        )

        self._history_service = (
            history_service or SignalHistoryService()
        )

    @property
    def history_service(self) -> SignalHistoryService:
        return self._history_service

    def register_signal(
        self,
        signal: SignalEvent,
        lifecycle: SignalLifecycle,
        occurred_at: datetime | None = None,
        reason: str = "Signal registered.",
    ) -> None:
        if lifecycle.status != "NEW":
            raise ValueError(
                "A newly registered signal must have NEW lifecycle status."
            )

        event = SignalTransitionEvent(
            signal_id=lifecycle.signal_id,
            previous_status=None,
            new_status="NEW",
            occurred_at=occurred_at or datetime.now(),
            reason=reason,
        )

        self._registry.register(
            signal,
            lifecycle,
        )

        self._history_service.record(event)

    def transition(
        self,
        signal_id: str,
        new_status: str,
        occurred_at: datetime | None = None,
        reason: str = "",
    ) -> SignalLifecycle:
        normalized_signal_id = signal_id.strip().upper()

        current_lifecycle = (
            self._registry.get_lifecycle(
                normalized_signal_id
            )
        )

        if current_lifecycle is None:
            raise ValueError(
                f"Signal '{normalized_signal_id}' is not registered."
            )

        updated_lifecycle = (
            self._lifecycle_service.transition(
                current_lifecycle,
                new_status,
            )
        )

        event = SignalTransitionEvent(
            signal_id=normalized_signal_id,
            previous_status=current_lifecycle.status,
            new_status=updated_lifecycle.status,
            occurred_at=occurred_at or datetime.now(),
            reason=reason,
        )

        self._registry.store_lifecycle(
            normalized_signal_id,
            updated_lifecycle,
        )

        self._history_service.record(event)

        return updated_lifecycle

    def activate(
        self,
        signal_id: str,
        occurred_at: datetime | None = None,
        reason: str = "",
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "ACTIVE",
            occurred_at,
            reason,
        )

    def mark_updated(
        self,
        signal_id: str,
        occurred_at: datetime | None = None,
        reason: str = "",
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "UPDATED",
            occurred_at,
            reason,
        )

    def expire(
        self,
        signal_id: str,
        occurred_at: datetime | None = None,
        reason: str = "",
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "EXPIRED",
            occurred_at,
            reason,
        )