from typing import Any

from app.services.major_structure_engine import MajorStructureEngine
from app.services.reference_level_service import ReferenceLevelService


class HigherTimeframeContextService:
    """
    Combines Daily structure, 4H structure, and previous-day
    reference levels into a higher-timeframe market context.

    Responsibilities:
        - Analyze Daily major structure.
        - Analyze 4H major structure.
        - Calculate PDH / PDL.
        - Compare Daily and 4H directions.
        - Determine higher-timeframe alignment.
        - Determine preferred trading direction.

    This service does NOT:
        - calculate risk
        - calculate position size
        - generate trade entries
        - analyze 15M/5M structure
        - make execution decisions

    PDH and PDL remain reference/liquidity levels and are
    deliberately kept separate from structural support/resistance.
    """

    def __init__(
        self,
        major_structure_engine: MajorStructureEngine | None = None,
        reference_level_service: ReferenceLevelService | None = None,
    ):
        self.major_structure_engine = (
            major_structure_engine
            or MajorStructureEngine()
        )

        self.reference_level_service = (
            reference_level_service
            or ReferenceLevelService()
        )

    def analyze(
        self,
        daily_candles: list[dict[str, Any]],
        four_hour_candles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze Daily structure, 4H structure, and previous-day
        reference levels.
        """

        daily = self.major_structure_engine.analyze(
            candles=daily_candles,
            timeframe="1day",
        )

        four_hour = self.major_structure_engine.analyze(
            candles=four_hour_candles,
            timeframe="4h",
        )

        reference_levels = (
            self.reference_level_service.analyze(
                daily_candles=daily_candles,
            )
        )

        daily_direction = daily["current_direction"]
        four_hour_direction = four_hour["current_direction"]

        alignment = self._determine_alignment(
            daily_direction=daily_direction,
            four_hour_direction=four_hour_direction,
        )

        preferred_direction = (
            self._determine_preferred_direction(
                alignment=alignment,
            )
        )

        return {
            "daily": daily,
            "four_hour": four_hour,

            "daily_direction": daily_direction,
            "four_hour_direction": four_hour_direction,

            "alignment": alignment,
            "preferred_direction": preferred_direction,

            "daily_protected_level": (
                daily["protected_level"]
            ),
            "four_hour_protected_level": (
                four_hour["protected_level"]
            ),

            "daily_major_support": (
                daily["major_support"]
            ),
            "daily_major_resistance": (
                daily["major_resistance"]
            ),

            "four_hour_major_support": (
                four_hour["major_support"]
            ),
            "four_hour_major_resistance": (
                four_hour["major_resistance"]
            ),

            "pdh": reference_levels["pdh"],
            "pdl": reference_levels["pdl"],
            "reference_date": (
                reference_levels["reference_date"]
            ),
        }

    @staticmethod
    def _determine_alignment(
        daily_direction: str,
        four_hour_direction: str,
    ) -> str:
        """
        Determine whether Daily and 4H structure agree.
        """

        if (
            daily_direction == "bullish"
            and four_hour_direction == "bullish"
        ):
            return "bullish"

        if (
            daily_direction == "bearish"
            and four_hour_direction == "bearish"
        ):
            return "bearish"

        if (
            daily_direction == "neutral"
            or four_hour_direction == "neutral"
        ):
            return "neutral"

        return "mixed"

    @staticmethod
    def _determine_preferred_direction(
        alignment: str,
    ) -> str:
        """
        Determine the preferred trading direction.

        Higher timeframe context provides directional preference.
        It does not create a trade entry.
        """

        if alignment == "bullish":
            return "BUY"

        if alignment == "bearish":
            return "SELL"

        return "WAIT"