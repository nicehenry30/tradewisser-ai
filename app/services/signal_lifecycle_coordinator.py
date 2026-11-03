from app.models.signal_lifecycle import SignalLifecycle
from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.signal_lifecycle_service import SignalLifecycleService


class SignalLifecycleCoordinator:
    """
    Coordinates signal lifecycle transitions.

    SignalLifecycleService remains responsible for deciding
    whether a transition is valid.

    ActiveSignalRegistry remains responsible for storing
    signal state.

    This coordinator connects those two responsibilities.
    """

    def __init__(
        self,
        registry: ActiveSignalRegistry,
        lifecycle_service: SignalLifecycleService | None = None,
    ):
        self._registry = registry
        self._lifecycle_service = (
            lifecycle_service
            or SignalLifecycleService()
        )

    def transition(
        self,
        signal_id: str,
        new_status: str,
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

        self._registry.store_lifecycle(
            normalized_signal_id,
            updated_lifecycle,
        )
        
        return updated_lifecycle

    def activate(
        self,
        signal_id: str,
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "ACTIVE",
        )

    def mark_updated(
        self,
        signal_id: str,
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "UPDATED",
        )

    def expire(
        self,
        signal_id: str,
    ) -> SignalLifecycle:
        return self.transition(
            signal_id,
            "EXPIRED",
        )