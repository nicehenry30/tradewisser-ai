from dataclasses import dataclass, field


@dataclass
class PreciseEntryEvaluation:
    direction: str
    timeframe: str

    setup_qualified: bool
    five_minute_confirmed: bool
    one_minute_confirmed: bool

    entry_ready: bool

    confirmations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "strategy": "precise_entry",
            "direction": self.direction,
            "timeframe": self.timeframe,
            "setup_qualified": self.setup_qualified,
            "five_minute_confirmed": self.five_minute_confirmed,
            "one_minute_confirmed": self.one_minute_confirmed,
            "entry_ready": self.entry_ready,
            "confirmations": self.confirmations,
            "contradictions": self.contradictions,
        }


class OneMinuteEntryEvaluator:
    """
    Evaluates the final 1M confirmation required for a precise entry.

    The 1M timeframe does not create the original setup.
    It provides the final entry confirmation after the
    higher-level setup and 5M confirmation are present.
    """

    TIMEFRAME = "1m"

    def evaluate(
        self,
        direction: str,
        setup_qualified: bool,
        five_minute_confirmed: bool,
        facts: dict,
    ) -> PreciseEntryEvaluation:

        if direction not in {"bullish", "bearish"}:
            raise ValueError("Direction must be 'bullish' or 'bearish'.")

        confirmations = []
        contradictions = []

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

        entry_ready = (
            setup_qualified
            and five_minute_confirmed
            and one_minute_confirmed
        )

        return PreciseEntryEvaluation(
            direction=direction,
            timeframe=self.TIMEFRAME,
            setup_qualified=setup_qualified,
            five_minute_confirmed=five_minute_confirmed,
            one_minute_confirmed=one_minute_confirmed,
            entry_ready=entry_ready,
            confirmations=confirmations,
            contradictions=contradictions,
        )