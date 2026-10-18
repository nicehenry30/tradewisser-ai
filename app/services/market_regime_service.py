from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarketRegimeResult:
    """
    Deterministic classification of the current market regime.

    This describes market condition.
    It does not decide whether a trade should be taken.
    """

    regime: str
    confidence: float
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime": self.regime,
            "confidence": self.confidence,
            "reasons": self.reasons,
        }


class MarketRegimeService:
    """
    Classifies the market into:

        - trending_bullish
        - trending_bearish
        - ranging
        - neutral

    This service does not reject low-volatility markets.

    Consolidation/ranging is a legitimate market condition.
    """

    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGING = "ranging"
    NEUTRAL = "neutral"

    def classify(
        self,
        analysis: dict[str, Any],
    ) -> MarketRegimeResult:
        trend = analysis.get("trend", "neutral")
        market_structure = analysis.get(
            "market_structure",
            {},
        )

        structure_direction = market_structure.get(
            "direction"
        )

        structure_strength = market_structure.get(
            "strength",
            0,
        )

        reasons: list[str] = []

        if (
            trend == "bullish"
            and structure_direction == "bullish"
        ):
            confidence = min(
                1.0,
                0.6 + (float(structure_strength) * 0.1),
            )

            reasons.append(
                "higher_analysis_and_structure_are_bullish"
            )

            return MarketRegimeResult(
                regime=self.TRENDING_BULLISH,
                confidence=confidence,
                reasons=reasons,
            )

        if (
            trend == "bearish"
            and structure_direction == "bearish"
        ):
            confidence = min(
                1.0,
                0.6 + (float(structure_strength) * 0.1),
            )

            reasons.append(
                "higher_analysis_and_structure_are_bearish"
            )

            return MarketRegimeResult(
                regime=self.TRENDING_BEARISH,
                confidence=confidence,
                reasons=reasons,
            )

        if (
            trend == "neutral"
            and structure_direction is None
        ):
            reasons.append(
                "trend_and_structure_do_not_show_directional_control"
            )

            return MarketRegimeResult(
                regime=self.RANGING,
                confidence=0.7,
                reasons=reasons,
            )

        reasons.append(
            "trend_and_structure_are_not_aligned"
        )

        return MarketRegimeResult(
            regime=self.NEUTRAL,
            confidence=0.5,
            reasons=reasons,
        )