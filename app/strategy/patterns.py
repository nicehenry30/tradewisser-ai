from dataclasses import dataclass
from typing import Literal


PatternDirection = Literal["bullish", "bearish"]
PatternType = Literal[
    "double_bottom",
    "double_top",
    "triple_bottom",
    "triple_top",
]


@dataclass(frozen=True)
class ReversalPattern:
    """
    Represents a detected reversal structure.

    The pattern can progress through several states:

        formation
            ↓
        structure_broken
            ↓
        waiting_for_pullback
            ↓
        entry_ready

    This class describes the structure only.
    It does not execute a trade.
    """

    pattern_type: PatternType
    direction: PatternDirection

    first_point: int
    second_point: int
    third_point: int | None

    first_price: float
    second_price: float
    third_price: float | None

    structure_level: float | None
    structure_broken: bool

    pullback_detected: bool
    entry_ready: bool

    valid: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "pattern_type": self.pattern_type,
            "direction": self.direction,
            "first_point": self.first_point,
            "second_point": self.second_point,
            "third_point": self.third_point,
            "first_price": self.first_price,
            "second_price": self.second_price,
            "third_price": self.third_price,
            "structure_level": self.structure_level,
            "structure_broken": self.structure_broken,
            "pullback_detected": self.pullback_detected,
            "entry_ready": self.entry_ready,
            "valid": self.valid,
            "reason": self.reason,
        }


class ReversalPatternDetector:
    """
    Detects the reversal structures taught for Tradewisser.

    This detector works with already identified swing points.

    It does not ask the LLM to identify structure.
    """

    def detect_double_bottom(
        self,
        first_low: dict,
        first_high: dict,
        second_low: dict,
        second_high: dict,
        pullback_detected: bool = False,
    ) -> ReversalPattern:

        first_low_price = float(first_low["price"])
        second_low_price = float(second_low["price"])
        first_high_price = float(first_high["price"])
        second_high_price = float(second_high["price"])

        if second_low_price < first_low_price:
            return ReversalPattern(
                pattern_type="double_bottom",
                direction="bullish",
                first_point=first_low["index"],
                second_point=second_low["index"],
                third_point=None,
                first_price=first_low_price,
                second_price=second_low_price,
                third_price=None,
                structure_level=first_high_price,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason=(
                    "Second low broke the first low. "
                    "The bullish double-bottom condition is invalid."
                ),
            )

        structure_broken = second_high_price > first_high_price

        if not structure_broken:
            return ReversalPattern(
                pattern_type="double_bottom",
                direction="bullish",
                first_point=first_low["index"],
                second_point=second_low["index"],
                third_point=None,
                first_price=first_low_price,
                second_price=second_low_price,
                third_price=None,
                structure_level=first_high_price,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=True,
                reason=(
                    "Valid double-bottom formation, but the second high "
                    "has not broken the first high yet."
                ),
            )

        entry_ready = pullback_detected

        if entry_ready:
            reason = (
                "Bullish double bottom confirmed. "
                "The second low protected the first low, "
                "the second high broke the first high, "
                "and a pullback was detected."
            )
        else:
            reason = (
                "Bullish double bottom confirmed and structure broken. "
                "Waiting for a pullback before entry."
            )

        return ReversalPattern(
            pattern_type="double_bottom",
            direction="bullish",
            first_point=first_low["index"],
            second_point=second_low["index"],
            third_point=None,
            first_price=first_low_price,
            second_price=second_low_price,
            third_price=None,
            structure_level=first_high_price,
            structure_broken=True,
            pullback_detected=pullback_detected,
            entry_ready=entry_ready,
            valid=True,
            reason=reason,
        )

    def detect_double_top(
        self,
        first_high: dict,
        first_low: dict,
        second_high: dict,
        second_low: dict,
        pullback_detected: bool = False,
    ) -> ReversalPattern:

        first_high_price = float(first_high["price"])
        second_high_price = float(second_high["price"])
        first_low_price = float(first_low["price"])
        second_low_price = float(second_low["price"])

        if second_high_price > first_high_price:
            return ReversalPattern(
                pattern_type="double_top",
                direction="bearish",
                first_point=first_high["index"],
                second_point=second_high["index"],
                third_point=None,
                first_price=first_high_price,
                second_price=second_high_price,
                third_price=None,
                structure_level=first_low_price,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason=(
                    "Second high broke the first high. "
                    "The bearish double-top condition is invalid."
                ),
            )

        structure_broken = second_low_price < first_low_price

        if not structure_broken:
            return ReversalPattern(
                pattern_type="double_top",
                direction="bearish",
                first_point=first_high["index"],
                second_point=second_high["index"],
                third_point=None,
                first_price=first_high_price,
                second_price=second_high_price,
                third_price=None,
                structure_level=first_low_price,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=True,
                reason=(
                    "Valid double-top formation, but the second low "
                    "has not broken the first low yet."
                ),
            )

        entry_ready = pullback_detected

        if entry_ready:
            reason = (
                "Bearish double top confirmed. "
                "The second high protected the first high, "
                "the second low broke the first low, "
                "and a pullback was detected."
            )
        else:
            reason = (
                "Bearish double top confirmed and structure broken. "
                "Waiting for a pullback before entry."
            )

        return ReversalPattern(
            pattern_type="double_top",
            direction="bearish",
            first_point=first_high["index"],
            second_point=second_high["index"],
            third_point=None,
            first_price=first_high_price,
            second_price=second_high_price,
            third_price=None,
            structure_level=first_low_price,
            structure_broken=True,
            pullback_detected=pullback_detected,
            entry_ready=entry_ready,
            valid=True,
            reason=reason,
        )

    def detect_triple_bottom(
        self,
        first_low: dict,
        second_low: dict,
        third_low: dict,
        structure_level: float,
        pullback_detected: bool = False,
    ) -> ReversalPattern:

        first_price = float(first_low["price"])
        second_price = float(second_low["price"])
        third_price = float(third_low["price"])

        if second_price < first_price:
            return ReversalPattern(
                pattern_type="triple_bottom",
                direction="bullish",
                first_point=first_low["index"],
                second_point=second_low["index"],
                third_point=third_low["index"],
                first_price=first_price,
                second_price=second_price,
                third_price=third_price,
                structure_level=structure_level,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason="Second low broke the first low.",
            )

        if third_price < second_price:
            return ReversalPattern(
                pattern_type="triple_bottom",
                direction="bullish",
                first_point=first_low["index"],
                second_point=second_low["index"],
                third_point=third_low["index"],
                first_price=first_price,
                second_price=second_price,
                third_price=third_price,
                structure_level=structure_level,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason="Third low broke the second low.",
            )

        entry_ready = pullback_detected

        return ReversalPattern(
            pattern_type="triple_bottom",
            direction="bullish",
            first_point=first_low["index"],
            second_point=second_low["index"],
            third_point=third_low["index"],
            first_price=first_price,
            second_price=second_price,
            third_price=third_price,
            structure_level=structure_level,
            structure_broken=True,
            pullback_detected=pullback_detected,
            entry_ready=entry_ready,
            valid=True,
            reason=(
                "Bullish triple bottom confirmed. "
                "Each subsequent low protected the previous low."
                + (
                    " Pullback detected."
                    if pullback_detected
                    else " Waiting for pullback."
                )
            ),
        )

    def detect_triple_top(
        self,
        first_high: dict,
        second_high: dict,
        third_high: dict,
        structure_level: float,
        pullback_detected: bool = False,
    ) -> ReversalPattern:

        first_price = float(first_high["price"])
        second_price = float(second_high["price"])
        third_price = float(third_high["price"])

        if second_price > first_price:
            return ReversalPattern(
                pattern_type="triple_top",
                direction="bearish",
                first_point=first_high["index"],
                second_point=second_high["index"],
                third_point=third_high["index"],
                first_price=first_price,
                second_price=second_price,
                third_price=third_price,
                structure_level=structure_level,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason="Second high broke the first high.",
            )

        if third_price > second_price:
            return ReversalPattern(
                pattern_type="triple_top",
                direction="bearish",
                first_point=first_high["index"],
                second_point=second_high["index"],
                third_point=third_high["index"],
                first_price=first_price,
                second_price=second_price,
                third_price=third_price,
                structure_level=structure_level,
                structure_broken=False,
                pullback_detected=False,
                entry_ready=False,
                valid=False,
                reason="Third high broke the second high.",
            )

        entry_ready = pullback_detected

        return ReversalPattern(
            pattern_type="triple_top",
            direction="bearish",
            first_point=first_high["index"],
            second_point=second_high["index"],
            third_point=third_high["index"],
            first_price=first_price,
            second_price=second_price,
            third_price=third_price,
            structure_level=structure_level,
            structure_broken=True,
            pullback_detected=pullback_detected,
            entry_ready=entry_ready,
            valid=True,
            reason=(
                "Bearish triple top confirmed. "
                "Each subsequent high protected the previous high."
                + (
                    " Pullback detected."
                    if pullback_detected
                    else " Waiting for pullback."
                )
            ),
        )