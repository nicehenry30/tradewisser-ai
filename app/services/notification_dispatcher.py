from dataclasses import dataclass

from app.models.signal_notification import SignalNotification
from app.services.notification_channel import NotificationChannel


@dataclass(frozen=True)
class NotificationDeliveryResult:
    """
    Describes the delivery outcome for one notification.
    """

    signal_id: str
    successful_channels: tuple[str, ...]
    failed_channels: tuple[str, ...]

    @property
    def delivered(self) -> bool:
        """
        Returns True when at least one channel
        successfully delivered the notification.
        """
        return bool(self.successful_channels)


class NotificationDispatcher:
    """
    Dispatches notifications through configured channels.

    A failure in one notification channel must not prevent
    other channels from receiving the notification.
    """

    def __init__(
        self,
        channels: list[NotificationChannel] | None = None,
    ):
        self._channels = list(channels or [])

    def dispatch(
        self,
        notification: SignalNotification,
    ) -> NotificationDeliveryResult:
        successful_channels: list[str] = []
        failed_channels: list[str] = []

        for channel in self._channels:
            try:
                delivered = channel.send(notification)

                if delivered:
                    successful_channels.append(channel.name)
                else:
                    failed_channels.append(channel.name)

            except Exception:
                failed_channels.append(channel.name)

        return NotificationDeliveryResult(
            signal_id=notification.signal_id,
            successful_channels=tuple(successful_channels),
            failed_channels=tuple(failed_channels),
        )