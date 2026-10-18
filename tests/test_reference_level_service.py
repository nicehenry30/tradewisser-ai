import unittest

from app.services.reference_level_service import (
    ReferenceLevelService,
)


class TestReferenceLevelService(unittest.TestCase):

    def setUp(self):
        self.service = ReferenceLevelService()

    @staticmethod
    def _candle(
        datetime,
        high,
        low,
    ):
        return {
            "datetime": datetime,
            "high": high,
            "low": low,
        }

    def test_pdh_and_pdl_are_calculated_from_previous_day(self):
        candles = [
            self._candle(
                "2026-01-01",
                100,
                90,
            ),
            self._candle(
                "2026-01-02",
                110,
                95,
            ),
            self._candle(
                "2026-01-03",
                120,
                100,
            ),
        ]

        result = self.service.analyze(candles)

        self.assertEqual(
            result["reference_date"],
            "2026-01-02",
        )

        self.assertEqual(
            result["pdh"],
            110.0,
        )

        self.assertEqual(
            result["pdl"],
            95.0,
        )

    def test_candles_are_sorted_before_previous_day_is_selected(self):
        candles = [
            self._candle(
                "2026-01-03",
                120,
                100,
            ),
            self._candle(
                "2026-01-01",
                100,
                90,
            ),
            self._candle(
                "2026-01-02",
                110,
                95,
            ),
        ]

        result = self.service.analyze(candles)

        self.assertEqual(
            result["reference_date"],
            "2026-01-02",
        )

        self.assertEqual(
            result["pdh"],
            110.0,
        )

        self.assertEqual(
            result["pdl"],
            95.0,
        )

    def test_insufficient_candles_are_rejected(self):
        candles = [
            self._candle(
                "2026-01-01",
                100,
                90,
            ),
        ]

        with self.assertRaises(ValueError):
            self.service.analyze(candles)

    def test_missing_high_is_rejected(self):
        candles = [
            {
                "datetime": "2026-01-01",
                "low": 90,
            },
            self._candle(
                "2026-01-02",
                110,
                95,
            ),
        ]

        with self.assertRaises(ValueError):
            self.service.analyze(candles)

    def test_missing_low_is_rejected(self):
        candles = [
            self._candle(
                "2026-01-01",
                100,
                90,
            ),
            {
                "datetime": "2026-01-02",
                "high": 110,
            },
        ]

        with self.assertRaises(ValueError):
            self.service.analyze(candles)


if __name__ == "__main__":
    unittest.main()