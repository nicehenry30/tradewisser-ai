from dataclasses import dataclass, field
from typing import Any

from app.strategy.patterns import ReversalPattern


@dataclass
class ReversalEvaluation:
    """
    Deterministic evaluation of a potential reversal setup.

    This evaluator combines:
    - market location
    - momentum
    - rejection
    - detected reversal structure
    - level confluence
    - lower-timeframe confirmation

    It does not execute trades.
    """

    direction: str

    location_confirmed: bool = False
    momentum_confirmed: bool = False
    rejection_confirmed: bool = False
    pattern_confirmed: bool = False
    confluence_confirmed: bool = False
    lower_timeframe_confirmed: bool = False

    pattern_type: str | None = None
    structure_broken: bool = False
    pullback_detected: bool = False
    entry_ready: bool = False

    confirmations: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    score: int = 0
    minimum_confirmations: int = 3
    qualified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": "reversal",
            "direction": self.direction,
            "location_confirmed": self.location_confirmed,
            "momentum_confirmed": self.momentum_confirmed,
            "rejection_confirmed": self.rejection_confirmed,
            "pattern_confirmed": self.pattern_confirmed,
            "confluence_confirmed": self.confluence_confirmed,
            "lower_timeframe_confirmed": self.lower_timeframe_confirmed,
            "pattern_type": self.pattern_type,
            "structure_broken": self.structure_broken,
            "pullback_detected": self.pullback_detected,
            "entry_ready": self.entry_ready,
            "confirmations": self.confirmations,
            "contradictions": self.contradictions,
            "score": self.score,
            "minimum_confirmations": self.minimum_confirmations,
            "qualified": self.qualified,
        }


class ReversalEvaluator:
    """
    Evaluates the user's reversal methodology.

    Market facts are calculated elsewhere.

    The evaluator combines those facts with an already detected
    reversal pattern.
    """

    def __init__(self, minimum_confirmations: int = 3):
        if minimum_confirmations < 1:
            raise ValueError(
                "minimum_confirmations must be at least 1."
            )

        self.minimum_confirmations = minimum_confirmations

    def evaluate(
        self,
        direction: str,
        facts: dict[str, Any],
        pattern: ReversalPattern | None = None,
    ) -> ReversalEvaluation:

        direction = direction.lower().strip()

        if direction not in {"bullish", "bearish"}:
            raise ValueError(
                "Reversal direction must be 'bullish' or 'bearish'."
            )

        evaluation = ReversalEvaluation(
            direction=direction,
            minimum_confirmations=self.minimum_confirmations,
        )

        # ---------------------------------------------------------------
        # 1. LOCATION
        # ---------------------------------------------------------------

        location_confirmed = any(
            (
                facts.get("at_daily_range_extreme"),
                facts.get("at_weekly_range_extreme"),
                facts.get("at_previous_day_level"),
                facts.get("at_previous_week_level"),
            )
        )

        if location_confirmed:
            evaluation.location_confirmed = True
            evaluation.confirmations.append("location")

        # ---------------------------------------------------------------
        # 2. MOMENTUM
        # ---------------------------------------------------------------

        if facts.get("momentum_confirmed"):
            evaluation.momentum_confirmed = True
            evaluation.confirmations.append("momentum")

        # ---------------------------------------------------------------
        # 3. REJECTION
        # ---------------------------------------------------------------

        if facts.get("rejection_confirmed"):
            evaluation.rejection_confirmed = True
            evaluation.confirmations.append("rejection")

        # ---------------------------------------------------------------
        # 4. REVERSAL PATTERN
        # ---------------------------------------------------------------

        if pattern is not None:

            # Make sure the detected pattern points in the same
            # direction as the requested reversal.
            if pattern.direction != direction:
                evaluation.contradictions.append(
                    "pattern_direction_mismatch"
                )

            elif pattern.valid:

                evaluation.pattern_type = pattern.pattern_type
                evaluation.structure_broken = (
                    pattern.structure_broken
                )
                evaluation.pullback_detected = (
                    pattern.pullback_detected
                )
                evaluation.entry_ready = (
                    pattern.entry_ready
                )

                evaluation.pattern_confirmed = True
                evaluation.confirmations.append(
                    pattern.pattern_type
                )

        # ---------------------------------------------------------------
        # 5. CANDLE CONFIRMATION
        # ---------------------------------------------------------------

        pin_bar = facts.get("pin_bar", False)
        engulfing = facts.get("engulfing", False)

        if pin_bar:
            evaluation.confirmations.append("pin_bar")

        if engulfing:
            evaluation.confirmations.append("engulfing")

        # A pin bar followed by an engulfing candle is a strong
        # reversal confirmation under the taught methodology.
        if pin_bar and engulfing:

            evaluation.rejection_confirmed = True

            if "rejection" not in evaluation.confirmations:
                evaluation.confirmations.append("rejection")

        # ---------------------------------------------------------------
        # 6. DAILY / WEEKLY CONFLUENCE
        # ---------------------------------------------------------------

        daily_confluence = facts.get(
            "daily_level_confluence",
            False,
        )

        weekly_confluence = facts.get(
            "weekly_level_confluence",
            False,
        )

        if daily_confluence or weekly_confluence:

            evaluation.confluence_confirmed = True

            evaluation.confirmations.append(
                "level_confluence"
            )

        # ---------------------------------------------------------------
        # 7. LOWER-TIMEFRAME CONFIRMATION
        # ---------------------------------------------------------------

        if facts.get("lower_timeframe_structure"):

            evaluation.lower_timeframe_confirmed = True

            evaluation.confirmations.append(
                "lower_timeframe_structure"
            )

        # ---------------------------------------------------------------
        # 8. CONTRADICTIONS
        # ---------------------------------------------------------------

        if facts.get(
            "strong_opposing_market_structure"
        ):

            evaluation.contradictions.append(
                "strong_opposing_market_structure"
            )

        # ---------------------------------------------------------------
        # 9. REMOVE DUPLICATES
        # ---------------------------------------------------------------

        evaluation.confirmations = list(
            dict.fromkeys(
                evaluation.confirmations
            )
        )

        evaluation.contradictions = list(
            dict.fromkeys(
                evaluation.contradictions
            )
        )

        # ---------------------------------------------------------------
        # 10. SCORE
        # ---------------------------------------------------------------

        evaluation.score = len(
            evaluation.confirmations
        )

        # ---------------------------------------------------------------
        # 11. QUALIFICATION
        # ---------------------------------------------------------------

        evaluation.qualified = (
            evaluation.score
            >= self.minimum_confirmations
            and not evaluation.contradictions
        )

        return evaluation