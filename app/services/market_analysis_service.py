class MarketAnalysisService:

    SWING_STRENGTH = 2

    def analyze(
        self,
        candles: list[dict],
    ) -> dict:

        if len(candles) < 20:
            raise ValueError(
                "At least 20 candles are required for market analysis."
            )

        candles = sorted(
            candles,
            key=lambda candle: candle["datetime"],
        )

        closes = [candle["close"] for candle in candles]

        ema_20 = self.calculate_ema(closes, 20)
        ema_50 = self.calculate_ema(closes, 50)
        rsi_14 = self.calculate_rsi(closes, 14)
        atr_14 = self.calculate_atr(candles, 14)

        trend = self.detect_trend(
            candles=candles,
            ema_20=ema_20,
            ema_50=ema_50,
        )

        swing_highs, swing_lows = self.find_swing_points(
            candles,
            strength=self.SWING_STRENGTH,
        )

        market_structure = self.classify_market_structure(
            swing_highs,
            swing_lows,
        )

        structure_events = self.detect_structure_events(
            candles=candles,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            strength=self.SWING_STRENGTH,
        )

        return {
            "latest_close": closes[-1],
            "ema_20": ema_20,
            "ema_50": ema_50,
            "rsi_14": rsi_14,
            "atr_14": atr_14,
            "trend": trend,
            "swing_highs": swing_highs,
            "swing_lows": swing_lows,
            "market_structure": market_structure,
            "structure_events": structure_events,
        }

    @staticmethod
    def calculate_ema(
        values: list[float],
        period: int,
    ) -> float:

        if len(values) < period:
            raise ValueError(
                f"At least {period} values are required for EMA."
            )

        multiplier = 2 / (period + 1)

        ema = sum(values[:period]) / period

        for value in values[period:]:
            ema = (
                (value - ema) * multiplier
            ) + ema

        return round(ema, 5)

    @staticmethod
    def calculate_rsi(
        closes: list[float],
        period: int = 14,
    ) -> float:

        if len(closes) <= period:
            raise ValueError(
                f"At least {period + 1} closes are required for RSI."
            )

        gains = []
        losses = []

        for index in range(1, len(closes)):
            change = closes[index] - closes[index - 1]

            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        average_gain = sum(gains[:period]) / period
        average_loss = sum(losses[:period]) / period

        for index in range(period, len(gains)):
            average_gain = (
                (average_gain * (period - 1))
                + gains[index]
            ) / period

            average_loss = (
                (average_loss * (period - 1))
                + losses[index]
            ) / period

        if average_loss == 0:
            return 100.0

        relative_strength = average_gain / average_loss

        rsi = 100 - (
            100 / (1 + relative_strength)
        )

        return round(rsi, 2)

    @staticmethod
    def calculate_atr(
        candles: list[dict],
        period: int = 14,
    ) -> float:

        if len(candles) <= period:
            raise ValueError(
                f"At least {period + 1} candles are required for ATR."
            )

        true_ranges = []

        for index, candle in enumerate(candles):

            high = candle["high"]
            low = candle["low"]

            if index == 0:
                previous_close = candle["close"]
            else:
                previous_close = candles[index - 1]["close"]

            true_range = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )

            true_ranges.append(true_range)

        atr = sum(true_ranges[:period]) / period

        for true_range in true_ranges[period:]:
            atr = (
                (atr * (period - 1))
                + true_range
            ) / period

        return round(atr, 5)

    @staticmethod
    def detect_trend(
        candles: list[dict],
        ema_20: float,
        ema_50: float,
    ) -> str:

        latest_close = candles[-1]["close"]

        if (
            latest_close > ema_20
            and ema_20 > ema_50
        ):
            return "bullish"

        if (
            latest_close < ema_20
            and ema_20 < ema_50
        ):
            return "bearish"

        return "neutral"

    @staticmethod
    def find_swing_points(
        candles: list[dict],
        strength: int = 2,
    ) -> tuple[list[dict], list[dict]]:

        swing_highs = []
        swing_lows = []

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
                swing_highs.append(
                    {
                        "index": index,
                        "datetime": current["datetime"],
                        "price": current["high"],
                    }
                )

            if is_swing_low:
                swing_lows.append(
                    {
                        "index": index,
                        "datetime": current["datetime"],
                        "price": current["low"],
                    }
                )

        return swing_highs, swing_lows

    @staticmethod
    def classify_market_structure(
        swing_highs: list[dict],
        swing_lows: list[dict],
    ) -> dict:

        high_structure = []
        low_structure = []

        for index in range(1, len(swing_highs)):

            previous = swing_highs[index - 1]
            current = swing_highs[index]

            if current["price"] > previous["price"]:
                classification = "HH"
            else:
                classification = "LH"

            high_structure.append(
                {
                    "index": current["index"],
                    "datetime": current["datetime"],
                    "price": current["price"],
                    "classification": classification,
                }
            )

        for index in range(1, len(swing_lows)):

            previous = swing_lows[index - 1]
            current = swing_lows[index]

            if current["price"] > previous["price"]:
                classification = "HL"
            else:
                classification = "LL"

            low_structure.append(
                {
                    "index": current["index"],
                    "datetime": current["datetime"],
                    "price": current["price"],
                    "classification": classification,
                }
            )

        return {
            "highs": high_structure,
            "lows": low_structure,
        }

    @staticmethod
    def detect_structure_events(
        candles: list[dict],
        swing_highs: list[dict],
        swing_lows: list[dict],
        strength: int = 2,
    ) -> list[dict]:

        events = []

        known_highs = []
        known_lows = []

        bias = None

        structural_high = None
        structural_low = None

        protected_high = None
        protected_low = None

        last_event_index = -1

        # --------------------------------------------------
        # Process candles chronologically.
        #
        # A swing is only allowed to influence structure
        # after it has been confirmed by `strength` candles.
        # --------------------------------------------------

        for candle_index, candle in enumerate(candles):

            close = candle["close"]

            # --------------------------------------------------
            # Confirm newly available swing highs/lows
            # --------------------------------------------------

            newly_confirmed_highs = [
                swing
                for swing in swing_highs
                if swing["index"] + strength == candle_index
            ]

            newly_confirmed_lows = [
                swing
                for swing in swing_lows
                if swing["index"] + strength == candle_index
            ]

            known_highs.extend(newly_confirmed_highs)
            known_lows.extend(newly_confirmed_lows)

            # ==================================================
            # 1. ESTABLISH INITIAL STRUCTURE
            # ==================================================

            if bias is None:

                # ----------------------------------------------
                # Look for a confirmed HH followed by a confirmed
                # HL. That gives us an initial bullish structure.
                # ----------------------------------------------

                if len(known_highs) >= 2 and len(known_lows) >= 2:

                    latest_high = known_highs[-1]
                    previous_high = known_highs[-2]

                    latest_low = known_lows[-1]
                    previous_low = known_lows[-2]

                    is_higher_high = (
                        latest_high["price"]
                        > previous_high["price"]
                    )

                    is_higher_low = (
                        latest_low["price"]
                        > previous_low["price"]
                    )

                    # HH occurred before HL.
                    if (
                        is_higher_high
                        and is_higher_low
                        and latest_high["index"]
                        < latest_low["index"]
                    ):

                        bias = "bullish"

                        structural_high = latest_high
                        protected_low = latest_low

                    # ------------------------------------------
                    # Look for LH + LL for initial bearish
                    # structure.
                    # ------------------------------------------

                    elif (
                        latest_high["price"]
                        < previous_high["price"]
                        and latest_low["price"]
                        < previous_low["price"]
                        and latest_high["index"]
                        < latest_low["index"]
                    ):

                        bias = "bearish"

                        structural_low = latest_low
                        protected_high = latest_high

            # ==================================================
            # 2. BULLISH STRUCTURE
            # ==================================================

            if bias == "bullish":

                # --------------------------------------------------
                # New confirmed highs can become the next structural
                # high only if they actually exceed the current one.
                # --------------------------------------------------

                for high in newly_confirmed_highs:

                    if (
                        structural_high is None
                        and high["index"] > last_event_index
                    ):
                        structural_high = high

                    elif (
                        structural_high is not None
                        and high["price"] > structural_high["price"]
                    ):
                        structural_high = high

                # --------------------------------------------------
                # A newly confirmed higher low becomes protected.
                # Only consider lows occurring after the structural
                # high.
                # --------------------------------------------------

                for low in newly_confirmed_lows:

                    if structural_high is None:
                        continue

                    if low["index"] <= structural_high["index"]:
                        continue

                    if (
                        protected_low is None
                        or low["price"] > protected_low["price"]
                    ):
                        protected_low = low

                # --------------------------------------------------
                # Bearish CHOCH
                # --------------------------------------------------

                if (
                    protected_low is not None
                    and candle_index > protected_low["index"]
                    and candle_index > last_event_index
                    and close < protected_low["price"]
                ):

                    broken_level = protected_low

                    # The most recently confirmed high becomes the
                    # protected high for the new bearish structure.
                    confirmed_highs = [
                        high
                        for high in known_highs
                        if high["index"] < candle_index
                    ]

                    if confirmed_highs:
                        new_protected_high = confirmed_highs[-1]
                    else:
                        new_protected_high = None

                    events.append(
                        {
                            "type": "CHOCH",
                            "direction": "bearish",
                            "broken_level": broken_level["price"],
                            "break_price": close,
                            "swing_datetime": broken_level["datetime"],
                            "break_datetime": candle["datetime"],
                            "swing_index": broken_level["index"],
                            "break_index": candle_index,
                        }
                    )

                    bias = "bearish"

                    protected_high = new_protected_high

                    structural_low = None
                    structural_high = None
                    protected_low = None

                    last_event_index = candle_index

                    continue

                # --------------------------------------------------
                # Bullish BOS
                # --------------------------------------------------

                if (
                    structural_high is not None
                    and candle_index > structural_high["index"]
                    and candle_index > last_event_index
                    and close > structural_high["price"]
                ):

                    broken_level = structural_high

                    events.append(
                        {
                            "type": "BOS",
                            "direction": "bullish",
                            "broken_level": broken_level["price"],
                            "break_price": close,
                            "swing_datetime": broken_level["datetime"],
                            "break_datetime": candle["datetime"],
                            "swing_index": broken_level["index"],
                            "break_index": candle_index,
                        }
                    )

                    # --------------------------------------------------
                    # IMPORTANT:
                    #
                    # The broken high is now consumed.
                    # We deliberately set it to None so the same
                    # level cannot produce BOS repeatedly.
                    # --------------------------------------------------

                    structural_high = None

                    last_event_index = candle_index

                    continue

            # ==================================================
            # 3. BEARISH STRUCTURE
            # ==================================================

            if bias == "bearish":

                # --------------------------------------------------
                # New confirmed lows can become the next structural
                # low only if they actually break lower.
                # --------------------------------------------------

                for low in newly_confirmed_lows:

                    if (
                        structural_low is None
                        and low["index"] > last_event_index
                    ):
                        structural_low = low

                    elif (
                        structural_low is not None
                        and low["price"] < structural_low["price"]
                    ):
                        structural_low = low

                # --------------------------------------------------
                # New lower highs become protected highs.
                # --------------------------------------------------

                for high in newly_confirmed_highs:

                    if structural_low is None:
                        continue

                    if high["index"] <= structural_low["index"]:
                        continue

                    if (
                        protected_high is None
                        or high["price"] < protected_high["price"]
                    ):
                        protected_high = high

                # --------------------------------------------------
                # Bullish CHOCH
                # --------------------------------------------------

                if (
                    protected_high is not None
                    and candle_index > protected_high["index"]
                    and candle_index > last_event_index
                    and close > protected_high["price"]
                ):

                    broken_level = protected_high

                    events.append(
                        {
                            "type": "CHOCH",
                            "direction": "bullish",
                            "broken_level": broken_level["price"],
                            "break_price": close,
                            "swing_datetime": broken_level["datetime"],
                            "break_datetime": candle["datetime"],
                            "swing_index": broken_level["index"],
                            "break_index": candle_index,
                        }
                    )

                    bias = "bullish"

                    structural_high = None
                    structural_low = None
                    protected_low = None
                    protected_high = None

                    last_event_index = candle_index

                    continue

                # --------------------------------------------------
                # Bearish BOS
                # --------------------------------------------------

                if (
                    structural_low is not None
                    and candle_index > structural_low["index"]
                    and candle_index > last_event_index
                    and close < structural_low["price"]
                ):

                    broken_level = structural_low

                    events.append(
                        {
                            "type": "BOS",
                            "direction": "bearish",
                            "broken_level": broken_level["price"],
                            "break_price": close,
                            "swing_datetime": broken_level["datetime"],
                            "break_datetime": candle["datetime"],
                            "swing_index": broken_level["index"],
                            "break_index": candle_index,
                        }
                    )

                    # Retire the broken level.
                    structural_low = None

                    last_event_index = candle_index

                    continue

        return events