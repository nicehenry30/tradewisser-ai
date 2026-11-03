from dataclasses import dataclass


@dataclass(frozen=True)
class SignalLifecycle:
    """
    Represents the current lifecycle state of a Tradewisser signal.

    The lifecycle model describes signal state only.
    It does not authorize trade execution.
    """

    signal_id: str
    status: str

    VALID_STATUSES = {
        "NEW",
        "ACTIVE",
        "UPDATED",
        "EXPIRED",
    }

    def __post_init__(self):
        normalized_signal_id = self.signal_id.strip().upper()
        normalized_status = self.status.strip().upper()

        if not normalized_signal_id:
            raise ValueError(
                "Signal ID must not be empty."
            )

        if normalized_status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid signal lifecycle status: {normalized_status}"
            )

        object.__setattr__(
            self,
            "signal_id",
            normalized_signal_id,
        )

        object.__setattr__(
            self,
            "status",
            normalized_status,
        )
