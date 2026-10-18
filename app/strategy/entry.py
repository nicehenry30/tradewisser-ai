from dataclasses import dataclass, field


@dataclass
class EntryEvaluation:
    direction: str

    setup_qualified: bool
    five_minute_confirmed: bool
    one_minute_confirmed: bool

    entry_authorized: bool

    confirmations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "strategy": "entry",
            "direction": self.direction,
            "setup_qualified": self.setup_qualified,
            "five_minute_confirmed": self.five_minute_confirmed,
            "one_minute_confirmed": self.one_minute_confirmed,
            "entry_authorized": self.entry_authorized,
            "confirmations": self.confirmations,
            "contradictions": self.contradictions,
        }


class EntryEvaluator:
    """
    Evaluates whether a qualified trading setup has reached
    the required 5M and 1M entry stages.

    Higher timeframes establish context.
    5M provides setup/confirmation.
    1M provides precise entry confirmation.
    """

    ALLOWED_ENTRY_TIMEFRAMES = {"5m", "1m"}

    def evaluate(
        self,
        direction: str,
        setup_qualified: bool,
        facts: dict,
    ) -> EntryEvaluation:

        if direction not in {"bullish", "bearish"}:
            raise ValueError("Direction must be 'bullish' or 'bearish'.")

        confirmations = []
        contradictions = []

        five_minute_confirmed = bool(
            facts.get("five_minute_confirmed", False)
        )

        one_minute_confirmed = bool(
            facts.get("one_minute_confirmed", False)
        )

        if setup_qualified:
            confirmations.append("qualified_setup")
        else:
            contradictions.append("setup_not_qualified")

        if five_minute_confirmed:
            confirmations.append("5m_confirmation")
        else:
            contradictions.append("5m_confirmation_missing")

        if one_minute_confirmed:
            confirmations.append("1m_confirmation")
        else:
            contradictions.append("1m_confirmation_missing")

        entry_authorized = (
            setup_qualified
            and five_minute_confirmed
            and one_minute_confirmed
        )

        return EntryEvaluation(
            direction=direction,
            setup_qualified=setup_qualified,
            five_minute_confirmed=five_minute_confirmed,
            one_minute_confirmed=one_minute_confirmed,
            entry_authorized=entry_authorized,
            confirmations=confirmations,
            contradictions=contradictions,
        )