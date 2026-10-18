import unittest

from app.services.higher_timeframe_context_service import (
    HigherTimeframeContextService,
)


class TestHigherTimeframeContextService(unittest.TestCase):

    def setUp(self):
        self.service = HigherTimeframeContextService()

    @staticmethod
    def _candle(
        datetime,
        high,
        low,
        close,
    ):
        return {
            "datetime": datetime,
            "high": high,
            "low": low,
            "close": close,
        }

    def _bullish_candles(self):
        return [
            self._candle("2026-01-01", 100, 95, 98),
            self._candle("2026-01-02", 102, 96, 100),
            self._candle("2026-01-03", 110, 100, 108),
            self._candle("2026-01-04", 105, 97, 102),
            self._candle("2026-01-05", 103, 90, 92),
            self._candle("2026-01-06", 106, 94, 104),
            self._candle("2026-01-07", 115, 103, 113),
            self._candle("2026-01-08", 110, 98, 105),
            self._candle("2026-01-09", 108, 93, 106),
            self._candle("2026-01-10", 112, 101, 110),
            self._candle("2026-01-11", 120, 108, 118),
        ]

    def _bearish_candles(self):
        return [
            self._candle("2026-01-01", 105, 100, 102),
            self._candle("2026-01-02", 104, 98, 100),
            self._candle("2026-01-03", 100, 90, 92),
            self._candle("2026-01-04", 103, 95, 101),
            self._candle("2026-01-05", 110, 97, 99),
            self._candle("2026-01-06", 106, 94, 96),
            self._candle("2026-01-07", 97, 85, 88),
            self._candle("2026-01-08", 102, 90, 98),
            self._candle("2026-01-09", 107, 92, 95),
            self._candle("2026-01-10", 99, 88, 90),
            self._candle("2026-01-11", 92, 80, 84),
        ]

    def test_bullish_alignment_allows_buy(self):
        result = self.service.analyze(
            daily_candles=self._bullish_candles(),
            four_hour_candles=self._bullish_candles(),
        )

        self.assertEqual(
            result["daily_direction"],
            "bullish",
        )

        self.assertEqual(
            result["four_hour_direction"],
            "bullish",
        )

        self.assertEqual(
            result["alignment"],
            "bullish",
        )

        self.assertEqual(
            result["preferred_direction"],
            "BUY",
        )

    def test_bearish_alignment_allows_sell(self):
        result = self.service.analyze(
            daily_candles=self._bearish_candles(),
            four_hour_candles=self._bearish_candles(),
        )

        self.assertEqual(
            result["daily_direction"],
            "bearish",
        )

        self.assertEqual(
            result["four_hour_direction"],
            "bearish",
        )

        self.assertEqual(
            result["alignment"],
            "bearish",
        )

        self.assertEqual(
            result["preferred_direction"],
            "SELL",
        )

    def test_bullish_daily_bearish_four_hour_is_mixed(self):
        result = self.service.analyze(
            daily_candles=self._bullish_candles(),
            four_hour_candles=self._bearish_candles(),
        )

        self.assertEqual(
            result["alignment"],
            "mixed",
        )

        self.assertEqual(
            result["preferred_direction"],
            "WAIT",
        )

    def test_bearish_daily_bullish_four_hour_is_mixed(self):
        result = self.service.analyze(
            daily_candles=self._bearish_candles(),
            four_hour_candles=self._bullish_candles(),
        )

        self.assertEqual(
            result["alignment"],
            "mixed",
        )

        self.assertEqual(
            result["preferred_direction"],
            "WAIT",
        )

    def test_pdh_and_pdl_are_included(self):
        result = self.service.analyze(
            daily_candles=self._bullish_candles(),
            four_hour_candles=self._bullish_candles(),
        )

        self.assertEqual(
            result["pdh"],
            112.0,
        )

        self.assertEqual(
            result["pdl"],
            101.0,
        )

        self.assertEqual(
            result["reference_date"],
            "2026-01-10",
        )


if __name__ == "__main__":
    unittest.main()