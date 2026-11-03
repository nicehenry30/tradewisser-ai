from app.models.signal_event import SignalEvent


class NotificationPolicy:
    """
    Determines whether a SignalEvent should generate
    a user-facing notification.

    This policy does not deliver notifications.
    It only decides whether notification is appropriate.
    """

    NOTIFIABLE_STATUSES = {
        "DEVELOPING",
        "CONFIRMED",
        "SIGNAL",
        "AUTHORIZED",
    }

    def should_notify(self, signal: SignalEvent) -> bool:
        """
        Return True when the signal deserves
        a user-facing notification.
        """
        return signal.status in self.NOTIFIABLE_STATUSES