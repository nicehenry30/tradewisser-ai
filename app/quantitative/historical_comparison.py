from __future__ import annotations

from statistics import mean, median
from typing import Any


class HistoricalConditionComparison:
    """
    Deterministic comparison of a current market condition against
    historical observations.

    This service does not produce BUY/SELL decisions.

    Its responsibility is to identify historically similar conditions
    and measure what happened afterward.
    """

    VERSION = "1.0"

    DEFAULT_TOLERANCES = {
        "rsi": 5.0,
        "volatility": 0.25,
        "price_vs_ema20": 0.01,
    }

    def compare(
        self,
        current: dict[str, float],
        historical: list[dict[str, Any]],
        tolerances: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        if not historical:
            raise ValueError(
                "Historical observations are required."
            )

        active_tolerances = {
            **self.DEFAULT_TOLERANCES,
            **(tolerances or {}),
        }

        matches = [
            observation
            for observation in historical
            if self._is_match(
                current,
                observation,
                active_tolerances,
            )
        ]

        forward_returns = [
            float(observation["forward_return"])
            for observation in matches
            if observation.get("forward_return") is not None
        ]

        favorable_moves = [
            float(observation["favorable_move"])
            for observation in matches
            if observation.get("favorable_move") is not None
        ]

        adverse_moves = [
            float(observation["adverse_move"])
            for observation in matches
            if observation.get("adverse_move") is not None
        ]

        return {
            "engine": "historical_condition_comparison",
            "version": self.VERSION,
            "current_condition": current,
            "matching": {
                "historical_observations": len(historical),
                "matches": len(matches),
                "match_rate": (
                    len(matches) / len(historical)
                    if historical
                    else None
                ),
                "tolerances": active_tolerances,
            },
            "outcomes": {
                "positive_rate": self._positive_rate(
                    forward_returns
                ),
                "negative_rate": self._negative_rate(
                    forward_returns
                ),
                "average_forward_return": (
                    mean(forward_returns)
                    if forward_returns
                    else None
                ),
                "median_forward_return": (
                    median(forward_returns)
                    if forward_returns
                    else None
                ),
                "average_favorable_move": (
                    mean(favorable_moves)
                    if favorable_moves
                    else None
                ),
                "average_adverse_move": (
                    mean(adverse_moves)
                    if adverse_moves
                    else None
                ),
            },
            "evidence": {
                "sample_size": len(forward_returns),
                "strength": self._evidence_strength(
                    len(forward_returns)
                ),
            },
        }

    @staticmethod
    def _is_match(
        current: dict[str, float],
        historical: dict[str, Any],
        tolerances: dict[str, float],
    ) -> bool:
        for feature, tolerance in tolerances.items():
            current_value = current.get(feature)
            historical_value = historical.get(feature)

            if current_value is None or historical_value is None:
                return False

            difference = abs(
                float(current_value)
                - float(historical_value)
            )

            if difference > float(tolerance):
                return False

        return True

    @staticmethod
    def _positive_rate(
        values: list[float],
    ) -> float | None:
        if not values:
            return None

        return sum(value > 0 for value in values) / len(values)

    @staticmethod
    def _negative_rate(
        values: list[float],
    ) -> float | None:
        if not values:
            return None

        return sum(value < 0 for value in values) / len(values)

    @staticmethod
    def _evidence_strength(sample_size: int) -> str:
        if sample_size >= 500:
            return "strong"

        if sample_size >= 100:
            return "moderate"

        if sample_size >= 30:
            return "limited"

        return "insufficient"