from app.models.signal_event import SignalEvent


class SignalDeduplicationService:
    """
    Prevents repeated proactive notifications for the same signal.

    Signal identity is based on:
        symbol + direction + status

    This service does not make trading decisions and does not
    authorize execution.
    """

    def __init__(self):
        self._registered_signals: set[tuple[str, str, str]] = set()

    def _signal_key(
        self,
        signal: SignalEvent,
    ) -> tuple[str, str, str]:
        return (
            signal.symbol.strip().upper(),
            signal.direction.strip().upper(),
            signal.status.strip().upper(),
        )

    def is_duplicate(self, signal: SignalEvent) -> bool:
        return self._signal_key(signal) in self._registered_signals

    def register(self, signal: SignalEvent) -> None:
        self._registered_signals.add(
            self._signal_key(signal)
        )

    def clear(self, signal: SignalEvent) -> None:
        self._registered_signals.discard(
            self._signal_key(signal)
        )
