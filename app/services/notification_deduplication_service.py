from app.models.signal_event import SignalEvent


class NotificationDeduplicationService:
    """
    Prevents identical signal states from generating
    repeated user-facing notifications.

    Deduplication is based on the signal's identity and
    notification-relevant state, not its reason text or
    detection timestamp.
    """

    def __init__(self):
        self._notified_signals: set[tuple[str, str, str]] = set()

    def _notification_key(
        self,
        signal: SignalEvent,
    ) -> tuple[str, str, str]:
        return (
            signal.symbol.strip().upper(),
            signal.direction.strip().upper(),
            signal.status.strip().upper(),
        )

    def is_duplicate(
        self,
        signal: SignalEvent,
    ) -> bool:
        return self._notification_key(signal) in self._notified_signals

    def register(
        self,
        signal: SignalEvent,
    ) -> None:
        self._notified_signals.add(
            self._notification_key(signal)
        )

    def clear(
        self,
        signal: SignalEvent,
    ) -> None:
        self._notified_signals.discard(
            self._notification_key(signal)
        )