from app.models.signal_lifecycle import SignalLifecycle


class SignalLifecycleService:
    """
    Controls valid state transitions for Tradewisser signals.

    This service manages signal lifecycle only.
    It does not make trading decisions and does not
    authorize trade execution.
    """

    VALID_TRANSITIONS = {
        "NEW": {"ACTIVE"},
        "ACTIVE": {"UPDATED", "EXPIRED"},
        "UPDATED": {"ACTIVE", "EXPIRED"},
        "EXPIRED": set(),
    }

    def transition(
        self,
        lifecycle: SignalLifecycle,
        new_status: str,
    ) -> SignalLifecycle:
        normalized_status = new_status.strip().upper()

        if normalized_status not in SignalLifecycle.VALID_STATUSES:
            raise ValueError(
                f"Invalid signal lifecycle status: {normalized_status}"
            )

        allowed_statuses = self.VALID_TRANSITIONS.get(
            lifecycle.status,
            set(),
        )

        if normalized_status not in allowed_statuses:
            raise ValueError(
                f"Invalid signal lifecycle transition: "
                f"{lifecycle.status} -> {normalized_status}"
            )

        return SignalLifecycle(
            signal_id=lifecycle.signal_id,
            status=normalized_status,
        )
