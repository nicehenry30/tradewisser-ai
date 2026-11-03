from abc import ABC, abstractmethod

from app.models.signal_notification import SignalNotification


class NotificationChannel(ABC):
    """
    Defines the contract for notification delivery channels.

    Concrete channels such as Flutter Push, Telegram,
    Email, or In-App notifications will implement this
    interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique name of the notification channel.
        """
        raise NotImplementedError

    @abstractmethod
    def send(
        self,
        notification: SignalNotification,
    ) -> bool:
        """
        Deliver a notification.

        Returns:
            True when delivery succeeds.
            False when delivery fails.
        """
        raise NotImplementedError