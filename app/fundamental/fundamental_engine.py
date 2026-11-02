from __future__ import annotations

from typing import Any

from app.models.fundamental_analysis import (
    CurrencyFundamentalSnapshot,
    FundamentalAnalysisResult,
)


class FundamentalAnalysisEngine:
    """
    Deterministic Forex fundamental-analysis engine.

    The engine compares the fundamental condition of the base
    and quote currencies.

    It produces evidence and interpretation, not a BUY/SELL
    trading instruction.
    """

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

    EVENT_LOW = "low"
    EVENT_MEDIUM = "medium"
    EVENT_HIGH = "high"

    BIAS_VALUES = {
        BULLISH: 1,
        NEUTRAL: 0,
        BEARISH: -1,
    }

    def analyze(
        self,
        symbol: str,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        upcoming_events: list[dict[str, Any]] | None = None,
    ) -> FundamentalAnalysisResult:
        """
        Analyze a Forex pair by comparing its base and quote
        currency fundamentals.
        """

        normalized_symbol = symbol.upper().strip()

        events = upcoming_events or []

        base_score = self._currency_score(base_snapshot)
        quote_score = self._currency_score(quote_snapshot)

        pair_score = base_score - quote_score

        direction = self._pair_direction(pair_score)

        confidence = self._confidence(
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            pair_score=pair_score,
        )

        event_risk = self._event_risk(events)

        key_drivers = self._build_key_drivers(
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            direction=direction,
        )

        risks = self._build_risks(
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            events=events,
            event_risk=event_risk,
        )

        summary = self._build_summary(
            symbol=normalized_symbol,
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            direction=direction,
            confidence=confidence,
            event_risk=event_risk,
            key_drivers=key_drivers,
            risks=risks,
        )

        return FundamentalAnalysisResult(
            symbol=normalized_symbol,
            base_currency=base_snapshot.currency,
            quote_currency=quote_snapshot.currency,
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            fundamental_direction=direction,
            confidence=confidence,
            event_risk=event_risk,
            upcoming_events=events,
            key_drivers=key_drivers,
            risks=risks,
            summary=summary,
        )

    def _currency_score(
        self,
        snapshot: CurrencyFundamentalSnapshot,
    ) -> float:
        """
        Calculate a deterministic composite fundamental score.

        Each available fundamental category contributes equally.
        """

        biases = [
            snapshot.inflation_bias,
            snapshot.growth_bias,
            snapshot.employment_bias,
            snapshot.monetary_policy_bias,
            snapshot.interest_rate_bias,
            snapshot.economic_surprise_bias,
        ]

        scores = [
            self.BIAS_VALUES.get(bias, 0)
            for bias in biases
        ]

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def _pair_direction(
        self,
        pair_score: float,
    ) -> str:
        if pair_score > 0.25:
            return self.BULLISH

        if pair_score < -0.25:
            return self.BEARISH

        return self.NEUTRAL

    def _confidence(
        self,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        pair_score: float,
    ) -> float:
        """
        Estimate confidence from:

        1. Currency-level confidence.
        2. Separation between base and quote fundamentals.
        """

        currency_confidence = (
            float(base_snapshot.confidence)
            + float(quote_snapshot.confidence)
        ) / 2.0

        separation = min(abs(pair_score), 1.0)

        confidence = (
            currency_confidence * 0.6
            + separation * 0.4
        )

        return round(
            max(0.0, min(confidence, 1.0)),
            4,
        )

    def _event_risk(
        self,
        events: list[dict[str, Any]],
    ) -> str:
        if not events:
            return self.EVENT_LOW

        highest_importance = 0

        for event in events:
            importance = str(
                event.get("importance", "")
            ).lower()

            if importance in {
                "high",
                "3",
                "critical",
            }:
                highest_importance = max(
                    highest_importance,
                    3,
                )
            elif importance in {
                "medium",
                "2",
            }:
                highest_importance = max(
                    highest_importance,
                    2,
                )
            elif importance in {
                "low",
                "1",
            }:
                highest_importance = max(
                    highest_importance,
                    1,
                )

        if highest_importance >= 3:
            return self.EVENT_HIGH

        if highest_importance == 2:
            return self.EVENT_MEDIUM

        return self.EVENT_LOW

    def _build_key_drivers(
        self,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        direction: str,
    ) -> list[str]:
        drivers: list[str] = []

        if direction == self.BULLISH:
            drivers.append(
                f"{base_snapshot.currency} fundamentals are "
                f"stronger relative to "
                f"{quote_snapshot.currency}"
            )

        elif direction == self.BEARISH:
            drivers.append(
                f"{quote_snapshot.currency} fundamentals are "
                f"stronger relative to "
                f"{base_snapshot.currency}"
            )

        else:
            drivers.append(
                f"{base_snapshot.currency} and "
                f"{quote_snapshot.currency} fundamentals "
                f"are relatively balanced"
            )

        drivers.extend(
            base_snapshot.key_drivers
        )

        drivers.extend(
            quote_snapshot.key_drivers
        )

        return drivers

    def _build_risks(
        self,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        events: list[dict[str, Any]],
        event_risk: str,
    ) -> list[str]:
        risks: list[str] = []

        risks.extend(base_snapshot.risks)
        risks.extend(quote_snapshot.risks)

        if event_risk == self.EVENT_HIGH:
            risks.append(
                "High-impact economic events may cause "
                "rapid changes in market expectations"
            )

        elif event_risk == self.EVENT_MEDIUM:
            risks.append(
                "Medium-impact economic events may alter "
                "the current fundamental assessment"
            )

        if events:
            risks.append(
                "Fundamental conditions can change after "
                "new economic data or central-bank communication"
            )

        return risks

    def _build_summary(
        self,
        symbol: str,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        direction: str,
        confidence: float,
        event_risk: str,
        key_drivers: list[str],
        risks: list[str],
    ) -> str:
        direction_text = direction.upper()

        summary_parts = [
            (
                f"{symbol} fundamental analysis is "
                f"{direction_text} with "
                f"{confidence:.0%} confidence."
            ),
            (
                f"{base_snapshot.currency} is assessed as "
                f"{base_snapshot.confidence:.0%} confidence "
                f"fundamental evidence, while "
                f"{quote_snapshot.currency} is assessed as "
                f"{quote_snapshot.confidence:.0%}."
            ),
            (
                f"Current event risk is "
                f"{event_risk.upper()}."
            ),
        ]

        if key_drivers:
            summary_parts.append(
                "Key driver: "
                + key_drivers[0]
                + "."
            )

        if risks:
            summary_parts.append(
                "Primary risk: "
                + risks[0]
                + "."
            )

        summary_parts.append(
            "This analysis represents fundamental evidence "
            "and does not constitute a trading instruction."
        )

        return " ".join(summary_parts)