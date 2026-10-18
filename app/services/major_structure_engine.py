from dataclasses import dataclass
from typing import Any


@dataclass
class MajorStructureEvent:
    """
    A confirmed structural event on the Daily or 4H timeframe.
    """

    index: int
    event_type: str
    direction: str
    broken_price: float
    break_price: float
    break_datetime: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "event_type": self.event_type,
            "direction": self.direction,
            "broken_price": self.broken_price,
            "break_price": self.break_price,
            "break_datetime": self.break_datetime,
        }


class MajorStructureEngine:
    """
    Major market-structure engine for Daily and 4H timeframes.

    Responsibilities:

        - Identify confirmed swing highs and lows.
        - Classify swings as HH, HL, LH, or LL.
        - Determine the major market direction.
        - Track protected structural levels.
        - Detect CHOCH and BOS events.
        - Identify major structural support and resistance.

    Timeframe hierarchy:

        1day -> macro / higher-timeframe context
        4h   -> major trading structure

    This engine deliberately does NOT calculate:

        - EMA
        - RSI
        - ATR
        - position size
        - risk
        - trade entries

    Those responsibilities belong to other components.
    """

    ALLOWED_TIMEFRAMES = {
        "1day",
        "4h",
    }

    DEFAULT_SWING_STRENGTH = 2

    def __init__(
        self,
        swing_strength: int = DEFAULT_SWING_STRENGTH,
    ):
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
        """
        Analyze major structure for Daily or 4H candles.
        """

        timeframe = timeframe.strip().lower()

        if timeframe not in self.ALLOWED_TIMEFRAMES:
            raise ValueError(
                "MajorStructureEngine supports only "
                "1day and 4h timeframes. "
                f"Received: {timeframe}"
            )

        normalized = self._normalize_candles(candles)

        minimum_candles = (
            (self.swing_strength * 2) + 3
        )

        if len(normalized) < minimum_candles:
            raise ValueError(
                f"At least {minimum_candles} candles are required "
                "for major structure analysis."
            )

        normalized.sort(
            key=lambda candle: candle["datetime"]
        )

        swings = self._find_swing_points(
            normalized
        )

        classification = self._classify_swings(
            swings
        )

        direction = self._determine_initial_direction(
            classification
        )

        protected_level = self._determine_protected_level(
            direction=direction,
            classification=classification,
        )

        events = self._detect_structure_events(
            candles=normalized,
            swings=swings,
            direction=direction,
            protected_level=protected_level,
        )

        current_direction = self._get_current_direction(
            initial_direction=direction,
            events=events,
        )

        current_protected_level = (
            self._get_current_protected_level(
                direction=current_direction,
                classification=classification,
                events=events,
            )
        )

        support = self._find_major_support(
            classification=classification,
            current_direction=current_direction,
            protected_level=current_protected_level,
        )

        resistance = self._find_major_resistance(
            classification=classification,
            current_direction=current_direction,
        )

        return {
            "timeframe": timeframe,
            "current_direction": current_direction,
            "initial_direction": direction,
            "swing_points": swings,
            "classification": classification,
            "protected_level": current_protected_level,
            "major_support": support,
            "major_resistance": resistance,
            "events": [
                event.to_dict()
                for event in events
            ],
        }

    @staticmethod
    def _normalize_candles(
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Validate and normalize candle data.
        """

        normalized = []

        for index, candle in enumerate(candles):

            required_fields = (
                "datetime",
                "high",
                "low",
                "close",
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
                    "close": float(candle["close"]),
                }
            )

        return normalized

    def _find_swing_points(
        self,
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Find confirmed fractal swing highs and lows.
        """

        strength = self.swing_strength
        swings = []

        for index in range(
            strength,
            len(candles) - strength,
        ):

            current = candles[index]

            left = candles[
                index - strength:index
            ]

            right = candles[
                index + 1:index + strength + 1
            ]

            is_swing_high = all(
                current["high"] > candle["high"]
                for candle in left + right
            )

            is_swing_low = all(
                current["low"] < candle["low"]
                for candle in left + right
            )

            if is_swing_high:
                swings.append(
                    {
                        "index": index,
                        "datetime": current["datetime"],
                        "point_type": "high",
                        "price": current["high"],
                    }
                )

            if is_swing_low:
                swings.append(
                    {
                        "index": index,
                        "datetime": current["datetime"],
                        "point_type": "low",
                        "price": current["low"],
                    }
                )

        swings.sort(
            key=lambda swing: swing["index"]
        )

        return swings

    @staticmethod
    def _classify_swings(
        swings: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Classify confirmed swings as:

            HH = Higher High
            HL = Higher Low
            LH = Lower High
            LL = Lower Low
        """

        highs = [
            swing
            for swing in swings
            if swing["point_type"] == "high"
        ]

        lows = [
            swing
            for swing in swings
            if swing["point_type"] == "low"
        ]

        high_structure = []

        for index in range(1, len(highs)):

            previous = highs[index - 1]
            current = highs[index]

            classification = (
                "HH"
                if current["price"] > previous["price"]
                else "LH"
            )

            high_structure.append(
                {
                    **current,
                    "classification": classification,
                }
            )

        low_structure = []

        for index in range(1, len(lows)):

            previous = lows[index - 1]
            current = lows[index]

            classification = (
                "HL"
                if current["price"] > previous["price"]
                else "LL"
            )

            low_structure.append(
                {
                    **current,
                    "classification": classification,
                }
            )

        return {
            "highs": high_structure,
            "lows": low_structure,
        }

    @staticmethod
    def _determine_initial_direction(
        classification: dict[str, list[dict[str, Any]]],
    ) -> str:
        """
        Determine the initial major direction from
        the latest confirmed structural classifications.
        """

        highs = classification["highs"]
        lows = classification["lows"]

        if not highs or not lows:
            return "neutral"

        latest_high = highs[-1]
        latest_low = lows[-1]

        if (
            latest_high["classification"] == "HH"
            and latest_low["classification"] == "HL"
        ):
            return "bullish"

        if (
            latest_high["classification"] == "LH"
            and latest_low["classification"] == "LL"
        ):
            return "bearish"

        return "neutral"

    @staticmethod
    def _determine_protected_level(
        direction: str,
        classification: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any] | None:

        if direction == "bullish":

            lows = classification["lows"]

            if lows:
                return lows[-1]

        if direction == "bearish":

            highs = classification["highs"]

            if highs:
                return highs[-1]

        return None




    def _detect_structure_events(
        self,
        candles: list[dict[str, Any]],
        swings: list[dict[str, Any]],
        direction: str,
        protected_level: dict[str, Any] | None,
    ) -> list[MajorStructureEvent]:
        """
        Detect structural CHOCH and BOS events chronologically.

        The engine must reconstruct structure from the beginning
        of the available dataset rather than using the final/latest
        structural classification as the starting point.

        This allows the engine to correctly detect sequences such as:

            Bullish
                ↓
            Bearish CHOCH
                ↓
            New bearish structural low
                ↓
            Bearish BOS

        and:

            Bearish
                ↓
            Bullish CHOCH
                ↓
            New bullish structural high
                ↓
            Bullish BOS

        CHOCH and BOS are structural events only.
        Entry priority is handled by a separate strategy layer.
        """

        events: list[MajorStructureEvent] = []

        if not swings:
            return events

        # ------------------------------------------------------------
        # Build chronological swing groups.
        # ------------------------------------------------------------

        highs = [
            swing
            for swing in swings
            if swing["point_type"] == "high"
        ]

        lows = [
            swing
            for swing in swings
            if swing["point_type"] == "low"
        ]

        # We need at least two highs and two lows to establish
        # an initial structural direction.
        if len(highs) < 2 or len(lows) < 2:
            return events

        # ------------------------------------------------------------
        # Determine the ORIGINAL structural direction.
        #
        # Important:
        # We intentionally use the first confirmed structure,
        # not the latest structure.
        # ------------------------------------------------------------

        first_high = highs[0]
        second_high = highs[1]

        first_low = lows[0]
        second_low = lows[1]

        if (
            second_high["price"] > first_high["price"]
            and second_low["price"] > first_low["price"]
        ):
            current_direction = "bullish"

            current_protected = second_low

        elif (
            second_high["price"] < first_high["price"]
            and second_low["price"] < first_low["price"]
        ):
            current_direction = "bearish"

            current_protected = second_high

        else:
            return events

        scan_index = 0

        # ------------------------------------------------------------
        # Walk forward through the structure.
        # ------------------------------------------------------------

        while scan_index < len(candles):

            if current_protected is None:
                break

            # ========================================================
            # BULLISH STRUCTURE
            # ========================================================

            if current_direction == "bullish":

                choch = self._find_bearish_choch(
                    candles=candles,
                    protected_level=current_protected,
                    start_index=scan_index,
                )

                if choch is None:
                    break

                events.append(choch)

                # After bearish CHOCH, wait for a NEW confirmed
                # structural low.
                next_low = self._find_next_swing_after(
                    swings=swings,
                    point_type="low",
                    index=choch.index,
                )

                if next_low is None:
                    break

                # Then wait for price to break that new bearish
                # structural low.
                bos = self._find_bos_after_swing(
                    candles=candles,
                    swing=next_low,
                    direction="bearish",
                )

                if bos is None:
                    break

                events.append(bos)

                current_direction = "bearish"

                # After bearish BOS, the next protected level
                # is the next confirmed structural high.
                current_protected = self._find_next_swing_after(
                    swings=swings,
                    point_type="high",
                    index=bos.index,
                )

                if current_protected is None:
                    break

                scan_index = current_protected["index"] + 1

                continue

            # ========================================================
            # BEARISH STRUCTURE
            # ========================================================

            if current_direction == "bearish":

                choch = self._find_bullish_choch(
                    candles=candles,
                    protected_level=current_protected,
                    start_index=scan_index,
                )

                if choch is None:
                    break

                events.append(choch)

                # After bullish CHOCH, wait for a NEW confirmed
                # structural high.
                next_high = self._find_next_swing_after(
                    swings=swings,
                    point_type="high",
                    index=choch.index,
                )

                if next_high is None:
                    break

                # Then wait for price to break that new bullish
                # structural high.
                bos = self._find_bos_after_swing(
                    candles=candles,
                    swing=next_high,
                    direction="bullish",
                )

                if bos is None:
                    break

                events.append(bos)

                current_direction = "bullish"

                # After bullish BOS, the next protected level
                # is the next confirmed structural low.
                current_protected = self._find_next_swing_after(
                    swings=swings,
                    point_type="low",
                    index=bos.index,
                )

                if current_protected is None:
                    break

                scan_index = current_protected["index"] + 1

                continue

            break

        return events

    @staticmethod
    def _find_next_swing_after(
        swings: list[dict[str, Any]],
        point_type: str,
        index: int,
    ) -> dict[str, Any] | None:
        """
        Find the first confirmed swing of the requested
        type after the supplied candle index.
        """

        for swing in swings:

            if (
                swing["point_type"] == point_type
                and swing["index"] > index
            ):
                return swing

        return None

    def _find_bos_after_swing(
        self,
        candles: list[dict[str, Any]],
        swing: dict[str, Any],
        direction: str,
    ) -> MajorStructureEvent | None:
        """
        Find the BOS that occurs after a new structural swing
        has become confirmed.
        """

        confirmation_index = (
            swing["index"] + self.swing_strength
        )

        start_index = confirmation_index + 1

        if start_index >= len(candles):
            return None

        for index in range(
            start_index,
            len(candles),
        ):

            candle = candles[index]

            # Bearish BOS:
            # price breaks below the new structural low.

            if (
                direction == "bearish"
                and candle["low"] < swing["price"]
            ):

                return MajorStructureEvent(
                    index=index,
                    event_type="BOS",
                    direction="bearish",
                    broken_price=swing["price"],
                    break_price=candle["close"],
                    break_datetime=candle["datetime"],
                )

            # Bullish BOS:
            # price breaks above the new structural high.

            if (
                direction == "bullish"
                and candle["high"] > swing["price"]
            ):

                return MajorStructureEvent(
                    index=index,
                    event_type="BOS",
                    direction="bullish",
                    broken_price=swing["price"],
                    break_price=candle["close"],
                    break_datetime=candle["datetime"],
                )

        return None

    def _find_bearish_choch(
        self,
        candles: list[dict[str, Any]],
        protected_level: dict[str, Any],
        start_index: int,
    ) -> MajorStructureEvent | None:
        """
        Find the first bearish CHOCH.

        A bearish CHOCH occurs when price breaks below
        the protected bullish structural low.
        """

        for index in range(
            start_index,
            len(candles),
        ):

            if index <= protected_level["index"]:
                continue

            candle = candles[index]

            if candle["low"] < protected_level["price"]:

                return MajorStructureEvent(
                    index=index,
                    event_type="CHOCH",
                    direction="bearish",
                    broken_price=protected_level["price"],
                    break_price=candle["close"],
                    break_datetime=candle["datetime"],
                )

        return None

    def _find_bullish_choch(
        self,
        candles: list[dict[str, Any]],
        protected_level: dict[str, Any],
        start_index: int,
    ) -> MajorStructureEvent | None:
        """
        Find the first bullish CHOCH.

        A bullish CHOCH occurs when price breaks above
        the protected bearish structural high.
        """

        for index in range(
            start_index,
            len(candles),
        ):

            if index <= protected_level["index"]:
                continue

            candle = candles[index]

            if candle["high"] > protected_level["price"]:

                return MajorStructureEvent(
                    index=index,
                    event_type="CHOCH",
                    direction="bullish",
                    broken_price=protected_level["price"],
                    break_price=candle["close"],
                    break_datetime=candle["datetime"],
                )

        return None

    @staticmethod
    def _latest_high_before(
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

    @staticmethod
    def _latest_low_before(
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

    @staticmethod
    def _get_current_direction(
        initial_direction: str,
        events: list[MajorStructureEvent],
    ) -> str:

        if not events:
            return initial_direction

        return events[-1].direction

    @staticmethod
    def _get_current_protected_level(
        direction: str,
        classification: dict[str, list[dict[str, Any]]],
        events: list[MajorStructureEvent],
    ) -> dict[str, Any] | None:

        if events:

            latest_event = events[-1]

            if latest_event.direction == "bullish":

                lows = classification["lows"]

                if lows:
                    return lows[-1]

            if latest_event.direction == "bearish":

                highs = classification["highs"]

                if highs:
                    return highs[-1]

        return MajorStructureEngine._determine_protected_level(
            direction=direction,
            classification=classification,
        )

    @staticmethod
    def _find_major_support(
        classification: dict[str, list[dict[str, Any]]],
        current_direction: str,
        protected_level: dict[str, Any] | None,
    ) -> dict[str, Any] | None:

        if protected_level is not None:

            if current_direction == "bullish":
                return protected_level

        lows = classification["lows"]

        if not lows:
            return None

        return lows[-1]

    @staticmethod
    def _find_major_resistance(
        classification: dict[str, list[dict[str, Any]]],
        current_direction: str,
    ) -> dict[str, Any] | None:

        highs = classification["highs"]

        if not highs:
            return None

        return highs[-1]