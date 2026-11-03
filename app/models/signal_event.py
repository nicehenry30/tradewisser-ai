from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SignalEvent:
    """
    Represents a meaningful market opportunity detected by Tradewisser.

    A SignalEvent is an informational market event. It does not
    authorize trade execution.
    """

    symbol: str
    direction: str
    status: str
    confidence: float
    reason: str
    detected_at: datetime

    VALID_DIRECTIONS = {"BUY", "SELL", "NEUTRAL"}

    VALID_STATUSES = {
        "WAIT",
        "POTENTIAL",
        "DEVELOPING",
        "CONFIRMED",
        "SIGNAL",
        "AUTHORIZED",
    }

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()
        normalized_direction = self.direction.strip().upper()
        normalized_status = self.status.strip().upper()

        if not normalized_symbol:
            raise ValueError("Signal symbol must not be empty.")

        if normalized_direction not in self.VALID_DIRECTIONS:
            raise ValueError(
                f"Invalid signal direction: {normalized_direction}"
            )

        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid signal status: {normalized_status}"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Signal confidence must be between 0.0 and 1.0."
            )

        if not self.reason.strip():
            raise ValueError("Signal reason must not be empty.")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "direction", normalized_direction)
        object.__setattr__(self, "status", normalized_status)
