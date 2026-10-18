import unittest

from app.services.major_structure_engine import MajorStructureEngine


class TestMajorStructureEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MajorStructureEngine()

    def _candle(self, datetime, high, low, close):
        return {
            "datetime": datetime,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
        }

    def _bullish_candles(self):
        return [
            self._candle("2026-01-01", 100, 95, 98),
            self._candle("2026-01-02", 102, 96, 100),
            self._candle("2026-01-03", 110, 100, 108),
            self._candle("2026-01-04", 105, 97, 101),
            self._candle("2026-01-05", 103, 90, 95),
            self._candle("2026-01-06", 106, 94, 102),
            self._candle("2026-01-07", 115, 103, 112),
            self._candle("2026-01-08", 110, 98, 105),
            self._candle("2026-01-09", 108, 93, 100),
            self._candle("2026-01-10", 112, 101, 109),
            self._candle("2026-01-11", 120, 108, 118),
        ]

    def _bearish_candles(self):
        return [
            self._candle("2026-01-01", 105, 100, 102),
            self._candle("2026-01-02", 104, 98, 100),
            self._candle("2026-01-03", 100, 90, 92),
            self._candle("2026-01-04", 103, 95, 99),
            self._candle("2026-01-05", 110, 97, 105),
            self._candle("2026-01-06", 106, 94, 101),
            self._candle("2026-01-07", 97, 85, 88),
            self._candle("2026-01-08", 102, 90, 95),
            self._candle("2026-01-09", 107, 92, 100),
            self._candle("2026-01-10", 99, 88, 93),
            self._candle("2026-01-11", 92, 80, 85),
        ]

    def test_daily_timeframe_is_supported(self):
        result = self.engine.analyze(
            self._bullish_candles(),
            "1day",
        )

        self.assertEqual(result["timeframe"], "1day")

    def test_four_hour_timeframe_is_supported(self):
        result = self.engine.analyze(
            self._bullish_candles(),
            "4h",
        )

        self.assertEqual(result["timeframe"], "4h")

    def test_unsupported_timeframe_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.analyze(
                self._bullish_candles(),
                "15m",
            )

    def test_bullish_structure_is_detected(self):
        result = self.engine.analyze(
            self._bullish_candles(),
            "1day",
        )

        print("\nBULLISH SWINGS:", result["swing_points"])
        print("BULLISH CLASSIFICATION:", result["classification"])
        print("BULLISH INITIAL:", result["initial_direction"])

        self.assertEqual(
            result["initial_direction"],
            "bullish",
        )

    def test_bearish_structure_is_detected(self):
        result = self.engine.analyze(
            self._bearish_candles(),
            "1day",
        )

        print("\nBEARISH SWINGS:", result["swing_points"])
        print("BEARISH CLASSIFICATION:", result["classification"])
        print("BEARISH INITIAL:", result["initial_direction"])

        self.assertEqual(
            result["initial_direction"],
            "bearish",
        )

    def test_bullish_to_bearish_choch(self):
        candles = self._bullish_candles()

        candles.extend([
            self._candle("2026-01-12", 110, 95, 100),
            self._candle("2026-01-13", 105, 91, 93),
            self._candle("2026-01-14", 103, 88, 90),
        ])

        result = self.engine.analyze(
            candles,
            "1day",
        )

        print(
            "\nBULLISH → BEARISH CHOCH EVENTS:",
            result["events"],
        )

        choch_events = [
            event
            for event in result["events"]
            if event["event_type"] == "CHOCH"
        ]

        self.assertGreaterEqual(
            len(choch_events),
            1,
        )

        self.assertEqual(
            choch_events[0]["direction"],
            "bearish",
        )

    def test_bearish_to_bullish_choch(self):
        candles = self._bearish_candles()

        candles.extend([
            self._candle("2026-01-12", 100, 80, 95),
            self._candle("2026-01-13", 105, 82, 102),
            self._candle("2026-01-14", 110, 85, 108),
        ])

        result = self.engine.analyze(
            candles,
            "1day",
        )

        print(
            "\nBEARISH → BULLISH CHOCH EVENTS:",
            result["events"],
        )

        choch_events = [
            event
            for event in result["events"]
            if event["event_type"] == "CHOCH"
        ]

        self.assertGreaterEqual(
            len(choch_events),
            1,
        )

        self.assertEqual(
            choch_events[0]["direction"],
            "bullish",
        )

    def test_bearish_bos_after_bullish_to_bearish_choch(self):
        candles = self._bullish_candles()

        candles.extend([
            self._candle("2026-01-12", 110, 95, 100),
            self._candle("2026-01-13", 105, 91, 93),

            self._candle("2026-01-14", 100, 90, 94),
            self._candle("2026-01-15", 102, 92, 98),
            self._candle("2026-01-16", 99, 88, 90),
            self._candle("2026-01-17", 101, 91, 95),
            self._candle("2026-01-18", 98, 90, 92),

            self._candle("2026-01-19", 95, 84, 86),
        ])

        result = self.engine.analyze(
            candles,
            "1day",
        )

        print(
            "\nBEARISH BOS EVENTS:",
            result["events"],
        )

        self.assertGreaterEqual(
            len(result["events"]),
            2,
        )

        self.assertEqual(
            result["events"][0]["event_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["events"][0]["direction"],
            "bearish",
        )

        self.assertEqual(
            result["events"][1]["event_type"],
            "BOS",
        )

        self.assertEqual(
            result["events"][1]["direction"],
            "bearish",
        )

    def test_bullish_bos_after_bearish_to_bullish_choch(self):
        candles = self._bearish_candles()

        candles.extend([
            self._candle("2026-01-12", 100, 80, 95),
            self._candle("2026-01-13", 105, 82, 102),
            self._candle("2026-01-14", 110, 85, 108),

            self._candle("2026-01-15", 100, 87, 94),
            self._candle("2026-01-16", 110, 88, 105),
            self._candle("2026-01-17", 115, 89, 112),
            self._candle("2026-01-18", 112, 87, 108),
            self._candle("2026-01-19", 111, 88, 109),

            self._candle("2026-01-20", 118, 90, 116),
        ])

        result = self.engine.analyze(
            candles,
            "1day",
        )

        print(
            "\nBULLISH BOS EVENTS:",
            result["events"],
        )

        self.assertGreaterEqual(
            len(result["events"]),
            2,
        )

        self.assertEqual(
            result["events"][0]["event_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["events"][0]["direction"],
            "bullish",
        )

        self.assertEqual(
            result["events"][1]["event_type"],
            "BOS",
        )

        self.assertEqual(
            result["events"][1]["direction"],
            "bullish",
        )


if __name__ == "__main__":
    unittest.main()