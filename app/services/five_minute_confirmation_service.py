from typing import Any

from app.services.structure_engine import StructureEngine
from app.strategy.reversal_family import ReversalFamilyDetector


class FiveMinuteConfirmationService:
    WAIT = "WAIT"
    DEVELOPING = "DEVELOPING"
    CONFIRMED = "CONFIRMED"

    def __init__(
        self,
        structure_engine: StructureEngine | None = None,
        reversal_family_detector: ReversalFamilyDetector | None = None,
    ):
        self.structure_engine = (
            structure_engine or StructureEngine()
        )

        self.reversal_family_detector = (
            reversal_family_detector
            or ReversalFamilyDetector()
        )

    def analyze(
        self,
        candles: list[dict[str, Any]],
        fifteen_minute_setup: dict[str, Any],
    ) -> dict[str, Any]:

        setup_qualified = fifteen_minute_setup.get(
            "qualified",
            False,
        )

        setup_direction = fifteen_minute_setup.get(
            "direction",
            "neutral",
        )

        setup_family = fifteen_minute_setup.get(
            "setup_family",
        )

        setup_type = fifteen_minute_setup.get(
            "setup_type",
        )

        expected_pattern = self._expected_pattern(
            fifteen_minute_setup
        )

        if not setup_qualified:
            return {
                "timeframe": "5m",
                "setup_family": setup_family,
                "setup_type": setup_type,
                "direction": setup_direction,
                "structure_direction": "neutral",
                "alignment": "not_aligned",
                "expected_pattern": expected_pattern,
                "structure_pattern": [],
                "confirmation_type": None,
                "confirmed": False,
                "status": self.WAIT,
                "reversal_family": {
                    "bullish": [],
                    "bearish": [],
                },
                "structure": None,
            }

        structure = self.structure_engine.analyze(
            candles=candles,
            timeframe="5m",
        )

        # ----------------------------------------------------------
        # 5M behavioural mirror
        #
        # The 5M inherits the 15M setup direction and pattern.
        # It does not create an independent directional thesis.
        #
        # ReversalFamilyDetector requires real OHLC candles.
        # Structure-only tests may provide lightweight fake values,
        # so only run the behavioural detector when valid OHLC
        # candle dictionaries are available.
        # ----------------------------------------------------------

        reversal_family = {
            "bullish": [],
            "bearish": [],
        }

        if self._has_ohlc_candles(candles):
            reversal_family = {
                "bullish": self.reversal_family_detector.detect(
                    candles=candles,
                    direction="bullish",
                    timeframe="5m",
                ),
                "bearish": self.reversal_family_detector.detect(
                    candles=candles,
                    direction="bearish",
                    timeframe="5m",
                ),
            }

        structure_direction = structure.get(
            "current_direction",
            "neutral",
        )

        alignment = self._alignment(
            setup_direction,
            structure_direction,
        )

        events = sorted(
            structure.get("events", []),
            key=lambda event: event.get(
                "index",
                -1,
            ),
        )

        confirmation_pattern = (
            self._detect_confirmation_pattern(
                events=events,
                expected_direction=setup_direction,
                expected_pattern=expected_pattern,
            )
        )

        pattern_complete = False

        if confirmation_pattern is not None:
            if len(expected_pattern) <= 1:
                pattern_complete = True
            elif confirmation_pattern == "_".join(
                expected_pattern
            ):
                pattern_complete = True

        confirmed = (
            alignment == "aligned"
            and pattern_complete
        )

        if confirmed:
            status = self.CONFIRMED
        elif (
            alignment == "aligned"
            and confirmation_pattern is not None
        ):
            status = self.DEVELOPING
        else:
            status = self.WAIT

        return {
            "timeframe": "5m",

            # Inherited directly from the 15M setup.
            "setup_family": setup_family,
            "setup_type": setup_type,
            "direction": setup_direction,
            "thesis_direction": setup_direction,

            # Lower-timeframe structure is evidence only.
            "structure_direction": structure_direction,
            "alignment": alignment,

            # The 5M mirrors the 15M expected structure.
            "expected_pattern": expected_pattern,
            "structure_pattern": (
                confirmation_pattern.split("_")
                if confirmation_pattern
                else []
            ),

            "confirmation_type": confirmation_pattern,
            "confirmed": confirmed,
            "status": status,
            "confirmation_state": status,

            # Behavioural evidence from the 5M.
            "reversal_family": reversal_family,

            # Raw lower-timeframe structure.
            "structure": structure,
        }

    @staticmethod
    def _has_ohlc_candles(
        candles: list[dict[str, Any]],
    ) -> bool:
        """
        Return True only when the supplied candles contain
        the OHLC fields required by ReversalFamilyDetector.

        This keeps structure-only tests and lightweight callers
        from invoking the detector with non-candle placeholders.
        """

        if not candles:
            return False

        required_fields = {
            "open",
            "high",
            "low",
            "close",
        }

        return all(
            isinstance(candle, dict)
            and required_fields.issubset(candle.keys())
            for candle in candles
        )

    @staticmethod
    def _alignment(
        setup_direction: str,
        structure_direction: str,
    ) -> str:

        if (
            setup_direction in {
                "bullish",
                "bearish",
            }
            and setup_direction
            == structure_direction
        ):
            return "aligned"

        return "not_aligned"

    @staticmethod
    def _expected_pattern(
        fifteen_minute_setup: dict[str, Any],
    ) -> list[str]:

        structure_pattern = (
            fifteen_minute_setup.get(
                "structure_pattern"
            )
        )

        if structure_pattern:
            return list(structure_pattern)

        setup_type = fifteen_minute_setup.get(
            "setup_type",
            "",
        )

        if "CHOCH_BOS" in setup_type:
            return ["CHOCH", "BOS"]

        if "CHOCH" in setup_type:
            return ["CHOCH"]

        if "BOS" in setup_type:
            return ["BOS"]

        return []

    @classmethod
    def _detect_confirmation_pattern(
        cls,
        events: list[dict[str, Any]],
        expected_direction: str,
        expected_pattern: list[str],
    ) -> str | None:

        if expected_direction not in {
            "bullish",
            "bearish",
        }:
            return None

        relevant_events = [
            event
            for event in events
            if event.get("direction")
            == expected_direction
        ]

        if not relevant_events:
            return None

        event_types = [
            event.get("event_type")
            for event in relevant_events
        ]

        # Complete CHOCH -> BOS sequence first.
        if (
            expected_pattern
            == ["CHOCH", "BOS"]
            and cls._contains_ordered_pattern(
                event_types,
                ["CHOCH", "BOS"],
            )
        ):
            return "CHOCH_BOS"

        # A 15M CHOCH+BOS setup may be developing
        # on 5M through either component.
        if expected_pattern == [
            "CHOCH",
            "BOS",
        ]:
            if "BOS" in event_types:
                return "BOS"

            if "CHOCH" in event_types:
                return "CHOCH"

            return None

        # A 15M CHOCH setup can be confirmed by
        # same-direction CHOCH or BOS on 5M.
        if expected_pattern == ["CHOCH"]:
            if "CHOCH" in event_types:
                return "CHOCH"

            if "BOS" in event_types:
                return "BOS"

            return None

        # A 15M BOS setup requires same-direction BOS.
        if expected_pattern == ["BOS"]:
            if "BOS" in event_types:
                return "BOS"

            return None

        return None

    @staticmethod
    def _contains_ordered_pattern(
        event_types: list[str | None],
        pattern: list[str],
    ) -> bool:

        if not pattern:
            return False

        pattern_index = 0

        for event_type in event_types:
            if event_type == pattern[pattern_index]:
                pattern_index += 1

                if pattern_index == len(pattern):
                    return True

        return False