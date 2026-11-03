from datetime import datetime

from app.models.signal_event import SignalEvent
from app.models.signal_notification import SignalNotification
from app.services.notification_deduplication_service import (
    NotificationDeduplicationService,
)
from app.services.notification_dispatcher import (
    NotificationDispatcher,
    NotificationDeliveryResult,
)
from app.services.notification_policy import NotificationPolicy


class SignalNotificationService:
    """
    Coordinates the creation and delivery of notifications
    generated from Tradewisser signal events.

    This service does not make trading decisions.

    Its responsibility is:

        SignalEvent
            ↓
        NotificationPolicy
            ↓
        Deduplication
            ↓
        SignalNotification
            ↓
        NotificationDispatcher
    """

    def __init__(
        self,
        policy: NotificationPolicy | None = None,
        deduplication_service: (
            NotificationDeduplicationService | None
        ) = None,
        dispatcher: NotificationDispatcher | None = None,
    ):
        self._policy = policy or NotificationPolicy()

        self._deduplication_service = (
            deduplication_service
            or NotificationDeduplicationService()
        )

        self._dispatcher = (
            dispatcher
            or NotificationDispatcher()
        )

    def notify(
        self,
        signal: SignalEvent,
        created_at: datetime | None = None,
    ) -> SignalNotification | None:
        """
        Create and dispatch a notification when the signal
        satisfies the notification policy and is not a duplicate.

        Returns:
            SignalNotification when a notification is created.
            None when notification is suppressed.
        """

        if not self._policy.should_notify(signal):
            return None

        if self._deduplication_service.is_duplicate(signal):
            return None

        notification = self._build_notification(
            signal,
            created_at or signal.detected_at,
        )

        self._dispatcher.dispatch(notification)

        self._deduplication_service.register(signal)

        return notification

    def notify_with_result(
        self,
        signal: SignalEvent,
        created_at: datetime | None = None,
    ) -> tuple[
        SignalNotification | None,
        NotificationDeliveryResult | None,
    ]:
        """
        Create and dispatch a notification while also returning
        the delivery result.
        """

        if not self._policy.should_notify(signal):
            return None, None

        if self._deduplication_service.is_duplicate(signal):
            return None, None

        notification = self._build_notification(
            signal,
            created_at or signal.detected_at,
        )

        delivery_result = self._dispatcher.dispatch(
            notification
        )

        self._deduplication_service.register(signal)

        return notification, delivery_result

    def _build_notification(
        self,
        signal: SignalEvent,
        created_at: datetime,
    ) -> SignalNotification:
        title = self._build_title(signal)

        message = self._build_message(signal)

        return SignalNotification(
            signal_id=self._build_signal_id(signal),
            symbol=signal.symbol,
            direction=signal.direction,
            status=signal.status,
            confidence=signal.confidence,
            title=title,
            message=message,
            created_at=created_at,
        )

    def _build_signal_id(
        self,
        signal: SignalEvent,
    ) -> str:
        return (
            f"{signal.symbol.strip().upper()}-"
            f"{signal.direction.strip().upper()}-"
            f"{signal.status.strip().upper()}"
        )

    def _build_title(
        self,
        signal: SignalEvent,
    ) -> str:
        if signal.status == "DEVELOPING":
            return (
                f"{signal.symbol} "
                f"{signal.direction} opportunity developing"
            )

        if signal.status == "SIGNAL":
            return (
                f"{signal.symbol} "
                f"{signal.direction} signal detected"
            )

        if signal.status == "AUTHORIZED":
            return (
                f"{signal.symbol} "
                f"{signal.direction} trade authorized"
            )

        return (
            f"{signal.symbol} "
            f"{signal.direction} market update"
        )

    def _build_message(
        self,
        signal: SignalEvent,
    ) -> str:
        confidence_percent = round(
            signal.confidence * 100
        )

        return (
            f"Status: {signal.status}. "
            f"Direction: {signal.direction}. "
            f"Confidence: {confidence_percent}%. "
            f"Reason: {signal.reason}"
        )