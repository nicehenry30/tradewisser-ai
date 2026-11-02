from __future__ import annotations

from typing import Any

from app.models.evidence import EvidenceObservation, EvidenceSource
from app.models.fundamental_analysis import FundamentalAnalysisResult


class EvidenceBuilder:
    """
    Converts outputs from Tradewisser's analytical services into
    the common Evidence Contract.

    This service does not make trading decisions.
    """

    def build_market_analysis(
        self,
        analysis: dict[str, Any],
    ) -> EvidenceSource:
        observations = [
            EvidenceObservation(
                name="trend",
                value=analysis.get("trend"),
                description="Current market trend identified by Market Analysis.",
            ),
            EvidenceObservation(
                name="market_structure",
                value=analysis.get("market_structure"),
                description="Current structural state of the market.",
            ),
            EvidenceObservation(
                name="latest_close",
                value=analysis.get("latest_close"),
                description="Latest analyzed closing price.",
            ),
            EvidenceObservation(
                name="ema_20",
                value=analysis.get("ema_20"),
                description="20-period exponential moving average.",
            ),
            EvidenceObservation(
                name="ema_50",
                value=analysis.get("ema_50"),
                description="50-period exponential moving average.",
            ),
            EvidenceObservation(
                name="rsi_14",
                value=analysis.get("rsi_14"),
                description="14-period relative strength index.",
            ),
            EvidenceObservation(
                name="atr_14",
                value=analysis.get("atr_14"),
                description="14-period average true range.",
            ),
            EvidenceObservation(
                name="structure_events",
                value=analysis.get("structure_events", []),
                description="Confirmed chronological BOS and CHOCH events.",
            ),
        ]

        direction = self._normalize_direction(
            analysis.get("trend")
        )

        return EvidenceSource(
            source="market_analysis",
            observations=observations,
            direction=direction,
            confidence=None,
            limitations=[
                "Market Analysis describes current price behavior and structure; it does not predict future outcomes."
            ],
        )

    def build_market_regime(
        self,
        regime: dict[str, Any],
    ) -> EvidenceSource:
        regime_name = regime.get("regime")
        confidence = regime.get("confidence")

        observations = [
            EvidenceObservation(
                name="regime",
                value=regime_name,
                description="Current market regime classification.",
            ),
            EvidenceObservation(
                name="reasons",
                value=regime.get("reasons", []),
                description="Reasons supporting the regime classification.",
            ),
        ]

        direction = self._regime_direction(regime_name)

        return EvidenceSource(
            source="market_regime",
            observations=observations,
            direction=direction,
            confidence=confidence,
            limitations=[
                "Market Regime classifies the current environment and does not independently determine trade entry."
            ],
        )
    
    def build_higher_timeframe_context(
        self,
        context: dict[str, Any],
    ) -> EvidenceSource:
        """
        Convert Higher-Timeframe Context into the common
        Evidence Contract.

        This is market-level contextual evidence.
        It does not determine the final trade action.
        """

        observations = [
            EvidenceObservation(
                name="daily_direction",
                value=context.get("daily_direction"),
                description="Current major direction on the Daily timeframe.",
            ),
            EvidenceObservation(
                name="four_hour_direction",
                value=context.get("four_hour_direction"),
                description="Current major direction on the 4H timeframe.",
            ),
            EvidenceObservation(
                name="alignment",
                value=context.get("alignment"),
                description="Alignment between Daily and 4H market structure.",
            ),
            EvidenceObservation(
                name="preferred_direction",
                value=context.get("preferred_direction"),
                description=(
                    "Contextual directional preference derived from "
                    "Daily and 4H alignment."
                ),
            ),
            EvidenceObservation(
                name="daily_protected_level",
                value=context.get("daily_protected_level"),
                description="Protected structural level on the Daily timeframe.",
            ),
            EvidenceObservation(
                name="four_hour_protected_level",
                value=context.get("four_hour_protected_level"),
                description="Protected structural level on the 4H timeframe.",
            ),
            EvidenceObservation(
                name="daily_major_support",
                value=context.get("daily_major_support"),
                description="Major Daily support level.",
            ),
            EvidenceObservation(
                name="daily_major_resistance",
                value=context.get("daily_major_resistance"),
                description="Major Daily resistance level.",
            ),
            EvidenceObservation(
                name="four_hour_major_support",
                value=context.get("four_hour_major_support"),
                description="Major 4H support level.",
            ),
            EvidenceObservation(
                name="four_hour_major_resistance",
                value=context.get("four_hour_major_resistance"),
                description="Major 4H resistance level.",
            ),
            EvidenceObservation(
                name="pdh",
                value=context.get("pdh"),
                description="Previous Day High reference level.",
            ),
            EvidenceObservation(
                name="pdl",
                value=context.get("pdl"),
                description="Previous Day Low reference level.",
            ),
            EvidenceObservation(
                name="reference_date",
                value=context.get("reference_date"),
                description="Date associated with the PDH and PDL reference levels.",
            ),
        ]

        direction = self._higher_timeframe_direction(
            context.get("alignment")
        )

        return EvidenceSource(
            source="higher_timeframe_context",
            observations=observations,
            direction=direction,
            confidence=None,
            limitations=[
                (
                    "Higher-Timeframe Context describes major market "
                    "structure, alignment, and reference levels; it "
                    "does not determine the final trade entry."
                )
            ],
        )

    @staticmethod
    def _higher_timeframe_direction(
        alignment: Any,
    ) -> str:
        if alignment == "bullish":
            return "bullish"

        if alignment == "bearish":
            return "bearish"

        return "neutral"

    def build_quantitative_analysis(
        self,
        quantitative: dict[str, Any],
    ) -> EvidenceSource:
        returns = quantitative.get("returns", {})
        forward_behavior = quantitative.get("forward_behavior", {})
        volatility = quantitative.get("volatility", {})
        sample = quantitative.get("sample", {})
        range_behavior = quantitative.get("range_behavior", {})

        positive_rate = forward_behavior.get("positive_rate")
        negative_rate = forward_behavior.get("negative_rate")

        observations = [
            EvidenceObservation(
                name="historical_positive_rate",
                value=positive_rate,
                unit="probability",
                description="Historical rate of positive forward outcomes.",
            ),
            EvidenceObservation(
                name="historical_negative_rate",
                value=negative_rate,
                unit="probability",
                description="Historical rate of negative forward outcomes.",
            ),
            EvidenceObservation(
                name="average_forward_return",
                value=forward_behavior.get("average_return"),
                unit="return",
                description="Average historical forward return.",
            ),
            EvidenceObservation(
                name="median_forward_return",
                value=forward_behavior.get("median_return"),
                unit="return",
                description="Median historical forward return.",
            ),
            EvidenceObservation(
                name="volatility",
                value=volatility,
                description="Historical volatility measurements and classification.",
            ),
            EvidenceObservation(
                name="range_behavior",
                value=range_behavior,
                description="Historical favorable and adverse price movement.",
            ),
            EvidenceObservation(
                name="latest_return",
                value=returns.get("latest"),
                unit="return",
                description="Most recent observed return.",
            ),
        ]

        direction = self._quantitative_direction(
            positive_rate,
            negative_rate,
        )

        return EvidenceSource(
            source="quantitative_analytics",
            observations=observations,
            direction=direction,
            confidence=None,
            sample_size=sample.get("forward_observations"),
            strength=None,
            limitations=[
                "Historical outcomes are evidence, not guarantees of future performance."
            ],
        )

    @staticmethod
    def _normalize_direction(value: Any) -> str:
        if value == "bullish":
            return "bullish"

        if value == "bearish":
            return "bearish"

        return "neutral"

    @staticmethod
    def _regime_direction(regime: Any) -> str:
        if regime == "trending_bullish":
            return "bullish"

        if regime == "trending_bearish":
            return "bearish"

        return "neutral"

    @staticmethod
    def _quantitative_direction(
        positive_rate: Any,
        negative_rate: Any,
    ) -> str:
        if positive_rate is None or negative_rate is None:
            return "neutral"

        if positive_rate > negative_rate:
            return "bullish"

        if negative_rate > positive_rate:
            return "bearish"

        return "neutral"

    def build_fundamental_analysis(
        self,
        result: FundamentalAnalysisResult,
    ) -> EvidenceSource:
        """
        Convert fundamental-analysis output into the unified
        EvidenceSource contract.

        Fundamental analysis provides macroeconomic evidence.
        It does not independently determine a trade entry.
        """

        direction = result.fundamental_direction

        observations = [
            EvidenceObservation(
                name="fundamental_direction",
                value=direction,
                description=(
                    "Relative fundamental assessment of the "
                    "base currency versus the quote currency."
                ),
            ),
            EvidenceObservation(
                name="confidence",
                value=result.confidence,
                unit="ratio",
                description=(
                    "Confidence in the fundamental assessment."
                ),
            ),
            EvidenceObservation(
                name="event_risk",
                value=result.event_risk,
                description=(
                    "Current risk from upcoming economic events."
                ),
            ),
            EvidenceObservation(
                name="base_currency",
                value=result.base_currency,
            ),
            EvidenceObservation(
                name="quote_currency",
                value=result.quote_currency,
            ),
            EvidenceObservation(
                name="summary",
                value=result.summary,
                description=(
                    "Human-readable fundamental assessment."
                ),
            ),
            EvidenceObservation(
                name="key_drivers",
                value=result.key_drivers,
            ),
            EvidenceObservation(
                name="risks",
                value=result.risks,
            ),
            EvidenceObservation(
                name="upcoming_events",
                value=result.upcoming_events,
            ),
        ]

        limitations = [
            "Fundamental analysis represents macroeconomic evidence "
            "and does not independently determine trade entry.",
            "Economic conditions can change after new data releases "
            "or central-bank communication.",
        ]

        if result.event_risk == "high":
            limitations.append(
                "High-impact economic events may cause rapid changes "
                "in market expectations and price volatility."
            )

        return EvidenceSource(
            source="fundamental_analysis",
            observations=observations,
            direction=direction,
            confidence=result.confidence,
            sample_size=None,
            strength=self._fundamental_strength(
                result.confidence
            ),
            limitations=limitations,
        )


    @staticmethod
    def _fundamental_strength(
        confidence: float,
    ) -> str:
        if confidence >= 0.75:
            return "strong"

        if confidence >= 0.50:
            return "moderate"

        return "weak"