from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SignalNotification:
    """
    Represents a notification generated from a Tradewisser signal.

    This model contains notification data only.
    It does not know how or where the notification
    will be delivered.
    """

    signal_id: str
    symbol: str
    direction: str
    status: str
    confidence: float
    title: str
    message: str
    created_at: datetime

    VALID_DIRECTIONS = {"BUY", "SELL", "NEUTRAL"}

    VALID_STATUSES = {
        "DEVELOPING",
        "CONFIRMED",
        "SIGNAL",
        "AUTHORIZED",
        "UPDATED",
        "EXPIRED",
    }

    def __post_init__(self):
        normalized_signal_id = self.signal_id.strip().upper()
        normalized_symbol = self.symbol.strip().upper()
        normalized_direction = self.direction.strip().upper()
        normalized_status = self.status.strip().upper()

        if not normalized_signal_id:
            raise ValueError(
                "Notification signal ID must not be empty."
            )

        if not normalized_symbol:
            raise ValueError(
                "Notification symbol must not be empty."
            )

        if normalized_direction not in self.VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid notification direction: "
                f"{normalized_direction}"
            )

        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid notification status: "
                f"{normalized_status}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Notification confidence must be between 0.0 and 1.0."
            )

        if not self.title.strip():
            raise ValueError(
                "Notification title must not be empty."
            )

        if not self.message.strip():
            raise ValueError(
                "Notification message must not be empty."
            )

        object.__setattr__(
            self,
            "signal_id",
            normalized_signal_id,
        )

        object.__setattr__(
            self,
            "symbol",
            normalized_symbol,
        )

        object.__setattr__(
            self,
            "direction",
            normalized_direction,
        )

        object.__setattr__(
            self,
            "status",
            normalized_status,
        )