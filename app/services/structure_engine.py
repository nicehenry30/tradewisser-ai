from dataclasses import dataclass
from typing import Any


@dataclass
class StructureEvent:
    index: int
    event_type: str
    direction: str
    broken_price: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "event_type": self.event_type,
            "direction": self.direction,
            "broken_price": self.broken_price,
        }


class StructureEngine:
    """
    Fractal market-structure engine.

    Intended timeframes:
        15M -> primary fractal structure
        5M  -> lower fractal / entry structure

    Methodology:

    Bullish structure:
        HH + HL
        break of protected HL -> bearish CHOCH
        next bearish structural low forms
        break of that low -> bearish BOS

    Bearish structure:
        LH + LL
        break of protected LH -> bullish CHOCH
        next bullish structural high forms
        break of that high -> bullish BOS

    After BOS, the engine continues looking for the next
    structural transition.

    CHOCH and BOS are therefore recurring structural events,
    not one-time events for the entire chart.
    """

    ALLOWED_TIMEFRAMES = {
        "15m",
        "5m",
    }

    def __init__(self, swing_strength: int = 1):
        if swing_strength < 1:
            raise ValueError(
                "swing_strength must be at least 1."
            )

        self.swing_strength = swing_strength

    def analyze(
        self,
        candles: list[dict[str, Any]],
        timeframe: str,
    ) -> dict[str, Any]:

        timeframe = timeframe.strip().lower()

        if timeframe not in self.ALLOWED_TIMEFRAMES:
            raise ValueError(
                f"StructureEngine supports only "
                f"15m and 5m. Received: {timeframe}"
            )

        normalized = self._normalize_candles(candles)

        if len(normalized) < 7:
            raise ValueError(
                "Not enough candles to analyze structure."
            )

        swings = self._find_swing_points(normalized)

        initial_structure = (
            self._find_initial_structure(swings)
        )

        if initial_structure is None:
            return {
                "timeframe": timeframe,
                "initial_direction": "neutral",
                "current_direction": "neutral",
                "current_state": "neutral",
                "swing_points": swings,
                "events": [],
                "movements": [],
            }

        events = self._track_structure(
            candles=normalized,
            swings=swings,
            initial_structure=initial_structure,
        )

        current_direction = (
            self._get_current_direction(
                initial_structure["direction"],
                events,
            )
        )

        current_state = (
            f"established_{current_direction}"
            if events
            else f"established_{initial_structure['direction']}"
        )

        return {
            "timeframe": timeframe,
            "initial_direction": initial_structure["direction"],
            "current_direction": current_direction,
            "current_state": current_state,
            "swing_points": swings,
            "events": [
                event.to_dict()
                for event in events
            ],
            "movements": self._build_movements(events),
        }

    def _normalize_candles(
        self,
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        normalized = []

        for index, candle in enumerate(candles):

            if "high" not in candle:
                raise ValueError(
                    f"Candle {index} is missing high."
                )

            if "low" not in candle:
                raise ValueError(
                    f"Candle {index} is missing low."
                )

            normalized.append(
                {
                    **candle,
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                }
            )

        return normalized

    def _find_swing_points(
        self,
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        strength = self.swing_strength
        swings = []

        for index in range(
            strength,
            len(candles) - strength,
        ):

            current_high = candles[index]["high"]
            current_low = candles[index]["low"]

            left = candles[
                index - strength:index
            ]

            right = candles[
                index + 1:index + strength + 1
            ]

            left_highs = [
                candle["high"]
                for candle in left
            ]

            right_highs = [
                candle["high"]
                for candle in right
            ]

            left_lows = [
                candle["low"]
                for candle in left
            ]

            right_lows = [
                candle["low"]
                for candle in right
            ]

            if (
                current_high > max(left_highs)
                and current_high > max(right_highs)
            ):
                swings.append(
                    {
                        "index": index,
                        "point_type": "high",
                        "price": current_high,
                    }
                )

            if (
                current_low < min(left_lows)
                and current_low < min(right_lows)
            ):
                swings.append(
                    {
                        "index": index,
                        "point_type": "low",
                        "price": current_low,
                    }
                )

        swings.sort(
            key=lambda swing: swing["index"]
        )

        return swings

    def _find_initial_structure(
        self,
        swings: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        highs = []
        lows = []

        for swing in swings:

            if swing["point_type"] == "high":
                highs.append(swing)

            else:
                lows.append(swing)

            if len(highs) < 2 or len(lows) < 2:
                continue

            previous_high = highs[-2]
            latest_high = highs[-1]

            previous_low = lows[-2]
            latest_low = lows[-1]

            if (
                latest_high["price"]
                > previous_high["price"]
                and latest_low["price"]
                > previous_low["price"]
            ):
                protected_low = latest_low

                if protected_low is not None:
                    return {
                        "direction": "bullish",
                        "protected_level": protected_low,
                        "start_index": latest_high["index"],
                    }

            if (
                latest_high["price"]
                < previous_high["price"]
                and latest_low["price"]
                < previous_low["price"]
            ):
                protected_high = latest_high

                if protected_high is not None:
                    return {
                        "direction": "bearish",
                        "protected_level": protected_high,
                        "start_index": latest_low["index"],
                    }

        return None

    def _latest_low_before(
        self,
        swings: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:

        candidates = [
            swing
            for swing in swings
            if (
                swing["point_type"] == "low"
                and swing["index"] < index
            )
        ]

        return candidates[-1] if candidates else None

    def _latest_high_before(
        self,
        swings: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:

        candidates = [
            swing
            for swing in swings
            if (
                swing["point_type"] == "high"
                and swing["index"] < index
            )
        ]

        return candidates[-1] if candidates else None

    def _track_structure(
        self,
        candles: list[dict[str, Any]],
        swings: list[dict[str, Any]],
        initial_structure: dict[str, Any],
    ) -> list[StructureEvent]:

        events = []

        direction = initial_structure["direction"]
        protected_level = initial_structure["protected_level"]

        scan_index = initial_structure["start_index"] + 1

        while scan_index < len(candles):

            if direction == "bullish":

                choch = self._find_bearish_choch(
                    candles,
                    protected_level,
                    scan_index,
                )

                if choch is None:
                    break

                events.append(choch)

                choch_index = choch.index

                bos = self._find_bearish_bos(
                    candles,
                    swings,
                    choch_index,
                )

                if bos is None:
                    break

                events.append(bos)

                direction = "bearish"

                protected_level = None

                scan_index = bos.index + 1

                protected_level = (
                    self._find_next_high_after(
                        swings,
                        bos.index,
                    )
                )

                if protected_level is None:
                    break

            else:

                choch = self._find_bullish_choch(
                    candles,
                    protected_level,
                    scan_index,
                )

                if choch is None:
                    break

                events.append(choch)

                choch_index = choch.index

                bos = self._find_bullish_bos(
                    candles,
                    swings,
                    choch_index,
                )

                if bos is None:
                    break

                events.append(bos)

                direction = "bullish"

                protected_level = None

                scan_index = bos.index + 1

                protected_level = (
                    self._find_next_low_after(
                        swings,
                        bos.index,
                    )
                )

                if protected_level is None:
                    break

        return events

    def _find_bearish_choch(
        self,
        candles: list[dict[str, Any]],
        protected_level: dict[str, Any],
        start_index: int,
    ) -> StructureEvent | None:

        for index in range(
            start_index,
            len(candles),
        ):

            if (
                candles[index]["low"]
                < protected_level["price"]
            ):
                return StructureEvent(
                    index=index,
                    event_type="CHOCH",
                    direction="bearish",
                    broken_price=protected_level["price"],
                )

        return None

    def _find_bullish_choch(
        self,
        candles: list[dict[str, Any]],
        protected_level: dict[str, Any],
        start_index: int,
    ) -> StructureEvent | None:

        for index in range(
            start_index,
            len(candles),
        ):

            if (
                candles[index]["high"]
                > protected_level["price"]
            ):
                return StructureEvent(
                    index=index,
                    event_type="CHOCH",
                    direction="bullish",
                    broken_price=protected_level["price"],
                )

        return None

    def _find_bearish_bos(
        self,
        candles: list[dict[str, Any]],
        swings: list[dict[str, Any]],
        choch_index: int,
    ) -> StructureEvent | None:

        next_low = self._find_next_low_after(
            swings,
            choch_index,
        )

        if next_low is None:
            return None

        for index in range(
            next_low["index"] + 1,
            len(candles),
        ):

            if (
                candles[index]["low"]
                < next_low["price"]
            ):
                return StructureEvent(
                    index=index,
                    event_type="BOS",
                    direction="bearish",
                    broken_price=next_low["price"],
                )

        return None

    def _find_bullish_bos(
        self,
        candles: list[dict[str, Any]],
        swings: list[dict[str, Any]],
        choch_index: int,
    ) -> StructureEvent | None:

        next_high = self._find_next_high_after(
            swings,
            choch_index,
        )

        if next_high is None:
            return None

        for index in range(
            next_high["index"] + 1,
            len(candles),
        ):

            if (
                candles[index]["high"]
                > next_high["price"]
            ):
                return StructureEvent(
                    index=index,
                    event_type="BOS",
                    direction="bullish",
                    broken_price=next_high["price"],
                )

        return None

    def _find_next_low_after(
        self,
        swings: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:

        for swing in swings:

            if (
                swing["point_type"] == "low"
                and swing["index"] > index
            ):
                return swing

        return None

    def _find_next_high_after(
        self,
        swings: list[dict[str, Any]],
        index: int,
    ) -> dict[str, Any] | None:

        for swing in swings:

            if (
                swing["point_type"] == "high"
                and swing["index"] > index
            ):
                return swing

        return None

    def _get_current_direction(
        self,
        initial_direction: str,
        events: list[StructureEvent],
    ) -> str:

        if not events:
            return initial_direction

        latest_bos = None

        for event in events:
            if event.event_type == "BOS":
                latest_bos = event

        if latest_bos is not None:
            return latest_bos.direction

        return initial_direction

    def _build_movements(
        self,
        events: list[StructureEvent],
    ) -> list[dict[str, Any]]:

        movements = []

        current = None

        for event in events:

            if event.event_type == "CHOCH":

                current = {
                    "direction": event.direction,
                    "choch": event.to_dict(),
                    "bos": None,
                    "status": "transitioning",
                }

                movements.append(current)

            elif (
                event.event_type == "BOS"
                and current is not None
            ):

                current["bos"] = event.to_dict()
                current["status"] = "established"

        return movements