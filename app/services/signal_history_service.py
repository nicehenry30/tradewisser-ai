from app.models.signal_transition_event import (
    SignalTransitionEvent,
)


class SignalHistoryService:
    """
    Stores and retrieves historical signal lifecycle events.

    This is currently an in-memory implementation.
    Database persistence will be introduced separately.

    The service records history only. It does not make
    trading decisions or change current lifecycle state.
    """

    def __init__(self) -> None:
        self._history: dict[
            str,
            list[SignalTransitionEvent],
        ] = {}

    def record(
        self,
        event: SignalTransitionEvent,
    ) -> None:
        if not isinstance(event, SignalTransitionEvent):
            raise TypeError(
                "Expected a SignalTransitionEvent instance."
            )

        signal_id = event.signal_id

        self._history.setdefault(
            signal_id,
            [],
        ).append(event)

    def get_history(
        self,
        signal_id: str,
    ) -> list[SignalTransitionEvent]:
        normalized_signal_id = signal_id.strip().upper()

        return list(
            self._history.get(
                normalized_signal_id,
                [],
            )
        )

    def get_latest(
        self,
        signal_id: str,
    ) -> SignalTransitionEvent | None:
        history = self.get_history(signal_id)

        if not history:
            return None

        return history[-1]

    def count(
        self,
        signal_id: str,
    ) -> int:
        return len(
            self.get_history(signal_id)
        )

    def list_signal_ids(self) -> list[str]:
        return sorted(self._history.keys())