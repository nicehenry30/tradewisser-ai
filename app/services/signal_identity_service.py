from app.models.signal_event import SignalEvent


class SignalIdentityService:
    """
    Creates stable identities for Tradewisser market opportunities.

    create_id()
        Returns the base identity for an opportunity.

    create_new_id()
        Creates a new sequential identity for a genuinely
        new opportunity of the same symbol and direction.

    Identity does not depend on AI wording, confidence,
    or detection time.
    """

    def __init__(self):
        self._sequences: dict[tuple[str, str], int] = {}

    def _base_key(
        self,
        signal: SignalEvent,
    ) -> tuple[str, str]:
        return (
            signal.symbol.strip().upper(),
            signal.direction.strip().upper(),
        )

    def create_id(self, signal: SignalEvent) -> str:
        symbol, direction = self._base_key(signal)

        return f"{symbol}-{direction}-001"

    def create_new_id(self, signal: SignalEvent) -> str:
        symbol, direction = self._base_key(signal)

        key = (symbol, direction)

        next_sequence = self._sequences.get(key, 0) + 1

        self._sequences[key] = next_sequence

        return f"{symbol}-{direction}-{next_sequence:03d}"
