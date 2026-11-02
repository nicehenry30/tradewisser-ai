from __future__ import annotations

from math import sqrt
from statistics import mean, median, pstdev
from typing import Any


class QuantitativeAnalytics:
    """
    Deterministic quantitative analysis of historical OHLCV candles.

    This service does not produce BUY/SELL decisions.

    Its responsibility is to measure historical price behavior and
    return structured evidence that Tradewisser AI can interpret.
    """

    MIN_CANDLES = 30

    def analyze(
        self,
        candles: list[dict[str, Any]],
        forward_bars: int = 5,
    ) -> dict[str, Any]:
        """
        Analyze historical candles.

        Parameters
        ----------
        candles:
            Chronological OHLCV candles.

        forward_bars:
            Number of completed candles used when measuring
            historical forward movement.

        Returns
        -------
        dict:
            Structured quantitative evidence.
        """

        if len(candles) < self.MIN_CANDLES:
            raise ValueError(
                f"Quantitative analysis requires at least "
                f"{self.MIN_CANDLES} candles."
            )

        if forward_bars < 1:
            raise ValueError("forward_bars must be at least 1.")

        ordered = sorted(
            candles,
            key=lambda candle: candle["datetime"],
        )

        closes = [float(candle["close"]) for candle in ordered]

        returns = self._returns(closes)

        volatility = self._volatility(returns)

        forward_returns = self._forward_returns(
            closes,
            forward_bars,
        )

        range_behavior = self._range_behavior(
            ordered,
            forward_bars,
        )

        return {
            "engine": "quantitative_analytics",
            "version": "1.0",

            "sample": {
                "candle_count": len(ordered),
                "return_observations": len(returns),
                "forward_observations": len(forward_returns),
                "forward_bars": forward_bars,
                "start": ordered[0]["datetime"],
                "end": ordered[-1]["datetime"],
            },

            "returns": {
                "average": self._safe_mean(returns),
                "median": self._safe_median(returns),
                "positive_rate": self._positive_rate(returns),
                "negative_rate": self._negative_rate(returns),
                "latest": returns[-1] if returns else None,
            },

            "volatility": volatility,

            "forward_behavior": {
                "average_return": self._safe_mean(forward_returns),
                "median_return": self._safe_median(forward_returns),
                "positive_rate": self._positive_rate(
                    forward_returns
                ),
                "negative_rate": self._negative_rate(
                    forward_returns
                ),
            },

            "range_behavior": range_behavior,
        }

    # ---------------------------------------------------------
    # Returns
    # ---------------------------------------------------------

    @staticmethod
    def _returns(closes: list[float]) -> list[float]:
        """
        Calculate simple percentage returns.

        return[t] = (close[t] - close[t-1]) / close[t-1]
        """

        results: list[float] = []

        for previous, current in zip(closes, closes[1:]):
            if previous == 0:
                continue

            results.append(
                (current - previous) / previous
            )

        return results

    # ---------------------------------------------------------
    # Volatility
    # ---------------------------------------------------------

    def _volatility(
        self,
        returns: list[float],
    ) -> dict[str, Any]:
        if not returns:
            return {
                "standard_deviation": None,
                "annualized_like": None,
                "percentile": None,
                "classification": "unknown",
            }

        standard_deviation = pstdev(returns)

        recent_window = returns[-20:]

        if len(returns) >= 20:
            current_volatility = pstdev(recent_window)
        else:
            current_volatility = standard_deviation

        percentile = self._percentile_rank(
            current_volatility,
            [
                pstdev(returns[:index])
                for index in range(
                    10,
                    len(returns) + 1,
                )
            ],
        )

        return {
            "standard_deviation": standard_deviation,
            "current": current_volatility,
            "percentile": percentile,
            "classification": self._classify_volatility(
                percentile
            ),
        }

    @staticmethod
    def _classify_volatility(
        percentile: float | None,
    ) -> str:
        if percentile is None:
            return "unknown"

        if percentile >= 80:
            return "high"

        if percentile <= 20:
            return "low"

        return "normal"

    # ---------------------------------------------------------
    # Forward behavior
    # ---------------------------------------------------------

    @staticmethod
    def _forward_returns(
        closes: list[float],
        forward_bars: int,
    ) -> list[float]:
        """
        Measure what happened after each historical observation.

        Important:
        These values are for historical evaluation only.
        They must never be used as information available at
        the original observation time.
        """

        results: list[float] = []

        last_valid_index = len(closes) - forward_bars

        for index in range(last_valid_index):
            current = closes[index]
            future = closes[index + forward_bars]

            if current == 0:
                continue

            results.append(
                (future - current) / current
            )

        return results

    # ---------------------------------------------------------
    # Range behavior
    # ---------------------------------------------------------

    @staticmethod
    def _range_behavior(
        candles: list[dict[str, Any]],
        forward_bars: int,
    ) -> dict[str, Any]:
        """
        Measure historical favorable/adverse movement.

        V1 uses percentage movement rather than ATR so that this
        module does not duplicate the existing ATR calculation
        inside MarketAnalysisService.
        """

        favorable: list[float] = []
        adverse: list[float] = []

        last_valid_index = len(candles) - forward_bars

        for index in range(last_valid_index):
            entry = float(candles[index]["close"])

            if entry == 0:
                continue

            future_window = candles[
                index + 1:index + forward_bars + 1
            ]

            highest = max(
                float(candle["high"])
                for candle in future_window
            )

            lowest = min(
                float(candle["low"])
                for candle in future_window
            )

            favorable_move = (highest - entry) / entry
            adverse_move = (lowest - entry) / entry

            favorable.append(favorable_move)
            adverse.append(adverse_move)

        return {
            "average_favorable_move": (
                mean(favorable)
                if favorable
                else None
            ),
            "median_favorable_move": (
                median(favorable)
                if favorable
                else None
            ),
            "average_adverse_move": (
                mean(adverse)
                if adverse
                else None
            ),
            "median_adverse_move": (
                median(adverse)
                if adverse
                else None
            ),
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _safe_mean(
        values: list[float],
    ) -> float | None:
        return mean(values) if values else None

    @staticmethod
    def _safe_median(
        values: list[float],
    ) -> float | None:
        return median(values) if values else None

    @staticmethod
    def _positive_rate(
        values: list[float],
    ) -> float | None:
        if not values:
            return None

        return sum(
            value > 0
            for value in values
        ) / len(values)

    @staticmethod
    def _negative_rate(
        values: list[float],
    ) -> float | None:
        if not values:
            return None

        return sum(
            value < 0
            for value in values
        ) / len(values)

    @staticmethod
    def _percentile_rank(
        value: float,
        historical_values: list[float],
    ) -> float | None:
        if not historical_values:
            return None

        less_than_or_equal = sum(
            historical_value <= value
            for historical_value in historical_values
        )

        return less_than_or_equal / len(
            historical_values
        )