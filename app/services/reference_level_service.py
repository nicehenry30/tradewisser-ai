from typing import Any


class ReferenceLevelService:
    """
    Calculates non-structural reference levels from daily candles.

    Current responsibilities:
        - Identify Previous Day High (PDH).
        - Identify Previous Day Low (PDL).

    These levels are reference/liquidity levels and are deliberately
    kept separate from structural support and resistance.

    This service does NOT:
        - detect HH / HL / LH / LL
        - detect CHOCH or BOS
        - determine market direction
        - generate trade entries
        - calculate risk
    """

    def analyze(
        self,
        daily_candles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Calculate PDH and PDL from daily candles.

        The candles may arrive in any order. They are sorted
        chronologically before the previous completed day is selected.
        """

        normalized = self._normalize_candles(
            daily_candles
        )

        if len(normalized) < 2:
            raise ValueError(
                "At least 2 daily candles are required "
                "to calculate PDH and PDL."
            )

        normalized.sort(
            key=lambda candle: candle["datetime"]
        )

        previous_day = normalized[-2]

        return {
            "reference_date": previous_day["datetime"],
            "pdh": previous_day["high"],
            "pdl": previous_day["low"],
        }

    @staticmethod
    def _normalize_candles(
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Validate and normalize daily candle data.
        """

        normalized = []

        for index, candle in enumerate(candles):

            required_fields = (
                "datetime",
                "high",
                "low",
            )

            for field in required_fields:
                if field not in candle:
                    raise ValueError(
                        f"Candle {index} is missing {field}."
                    )

            normalized.append(
                {
                    **candle,
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                }
            )

        return normalized