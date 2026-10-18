from dataclasses import dataclass, field


@dataclass
class ConfirmationEvaluation:
    direction: str
    timeframe: str
    setup_qualified: bool
    direction_confirmed: bool
    structure_confirmed: bool
    confirmed: bool
    confirmations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "strategy": "confirmation",
            "direction": self.direction,
            "timeframe": self.timeframe,
            "setup_qualified": self.setup_qualified,
            "direction_confirmed": self.direction_confirmed,
            "structure_confirmed": self.structure_confirmed,
            "confirmed": self.confirmed,
            "confirmations": self.confirmations,
            "contradictions": self.contradictions,
        }


class FiveMinuteConfirmationEvaluator:
    """
    Evaluates the 5M confirmation layer.

    Important:
    - MarketAnalysisService provides observations.
    - MarketConfirmationAdapter translates those observations into facts.
    - This evaluator decides whether the supplied 5M facts support
      the requested direction.

    This layer does NOT create a complete entry signal.
    """

    TIMEFRAME = "5m"

    def evaluate(self, direction, setup_qualified, facts):
        if direction not in {"bullish", "bearish"}:
            raise ValueError("direction must be 'bullish' or 'bearish'")

        direction_confirmed = bool(
            facts.get("direction_confirmed", False)
        )

        structure_confirmed = bool(
            facts.get("structure_confirmed", False)
        )

        opposing_structure = bool(
            facts.get("opposing_structure", False)
        )

        confirmations = []
        contradictions = []

        if setup_qualified:
            confirmations.append("qualified_setup")

        if direction_confirmed:
            confirmations.append("5m_direction")
        else:
            contradictions.append("5m_direction_not_confirmed")

        if structure_confirmed:
            confirmations.append("5m_structure")
        else:
            contradictions.append("5m_structure_not_confirmed")

        if opposing_structure:
            contradictions.append("5m_opposing_structure")

        confirmed = (
            setup_qualified
            and direction_confirmed
            and structure_confirmed
            and not opposing_structure
        )

        return ConfirmationEvaluation(
            direction=direction,
            timeframe=self.TIMEFRAME,
            setup_qualified=setup_qualified,
            direction_confirmed=direction_confirmed,
            structure_confirmed=structure_confirmed,
            confirmed=confirmed,
            confirmations=confirmations,
            contradictions=contradictions,
        )