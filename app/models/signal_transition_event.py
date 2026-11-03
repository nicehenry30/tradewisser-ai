from dataclasses import dataclass
from datetime import datetime

from app.models.signal_lifecycle import SignalLifecycle


@dataclass(frozen=True)
class SignalTransitionEvent:
    """
    Immutable historical record of a signal lifecycle transition.

    This model records what happened to a signal.
    It does not manage lifecycle state or authorize trades.
    """

    signal_id: str
    previous_status: str | None
    new_status: str
    occurred_at: datetime
    reason: str = ""

    def __post_init__(self) -> None:
        normalized_signal_id = self.signal_id.strip().upper()
        normalized_new_status = self.new_status.strip().upper()

        normalized_previous_status = (
            self.previous_status.strip().upper()
            if self.previous_status is not None
            else None
        )

        if not normalized_signal_id:
            raise ValueError("Signal ID must not be empty.")

        valid_statuses = SignalLifecycle.VALID_STATUSES

        if normalized_new_status not in valid_statuses:
            raise ValueError(
                f"Invalid new lifecycle status: {normalized_new_status}"
            )

        if (
            normalized_previous_status is not None
            and normalized_previous_status not in valid_statuses
        ):
            raise ValueError(
                "Invalid previous lifecycle status: "
                f"{normalized_previous_status}"
            )

        if normalized_previous_status == normalized_new_status:
            raise ValueError(
                "Previous and new lifecycle statuses must be different."
            )

        if not isinstance(self.occurred_at, datetime):
            raise ValueError(
                "Transition timestamp must be a datetime object."
            )

        object.__setattr__(
            self,
            "signal_id",
            normalized_signal_id,
        )

        object.__setattr__(
            self,
            "previous_status",
            normalized_previous_status,
        )

        object.__setattr__(
            self,
            "new_status",
            normalized_new_status,
        )

        object.__setattr__(
            self,
            "reason",
            self.reason.strip(),
        )