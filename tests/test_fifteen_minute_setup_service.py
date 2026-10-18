import unittest
from app.services.structure_engine import StructureEngine

from app.services.fifteen_minute_setup_service import (
    FifteenMinuteSetupService,
)


class FakeStructureEngine:

    def __init__(self, result):
        self.result = result

    def analyze(self, candles, timeframe):
        self.received_candles = candles
        self.received_timeframe = timeframe
        return self.result


class TestFifteenMinuteSetupService(unittest.TestCase):

    @staticmethod
    def _structure(
        current_direction,
        events,
    ):
        return {
            "timeframe": "15m",
            "initial_direction": current_direction,
            "current_direction": current_direction,
            "current_state": (
                f"established_{current_direction}"
            ),
            "swing_points": [],
            "events": events,
            "movements": [],
        }

    @staticmethod
    def _event(
        index,
        event_type,
        direction,
    ):
        return {
            "index": index,
            "event_type": event_type,
            "direction": direction,
            "broken_price": 100.0,
        }

    def test_real_structure_engine_detects_bullish_choch_setup(self):
        candles = [
            {"datetime": "2026-02-01 00:00", "high": 100, "low": 95},
            {"datetime": "2026-02-01 00:15", "high": 105, "low": 97},
            {"datetime": "2026-02-01 00:30", "high": 102, "low": 94},
            {"datetime": "2026-02-01 00:45", "high": 104, "low": 96},
            {"datetime": "2026-02-01 01:00", "high": 101, "low": 93},
            {"datetime": "2026-02-01 01:15", "high": 103, "low": 95},
            {"datetime": "2026-02-01 01:30", "high": 99, "low": 91},
            {"datetime": "2026-02-01 01:45", "high": 106, "low": 94},
            {"datetime": "2026-02-01 02:00", "high": 109, "low": 97},
            {"datetime": "2026-02-01 02:15", "high": 111, "low": 99},
            {"datetime": "2026-02-01 02:30", "high": 113, "low": 101},
        ]
        service = FifteenMinuteSetupService(
            structure_engine=StructureEngine()
        )

        result = service.analyze(
            candles=candles,
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["structure_direction"],
            "bearish",
        )

        self.assertEqual(
            result["setup_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["setup_priority"],
            "primary",
        )

        self.assertTrue(
            result["qualified"]
        )

        self.assertEqual(
            result["latest_choch"]["direction"],
            "bullish",
        )



    def test_bullish_choch_is_primary_setup(self):
        structure = self._structure(
            "bullish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bullish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertEqual(
            result["setup_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["setup_priority"],
            "primary",
        )

        self.assertTrue(
            result["qualified"]
        )

    def test_bullish_bos_is_secondary_setup(self):
        structure = self._structure(
            "bullish",
            [
                self._event(
                    10,
                    "BOS",
                    "bullish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["setup_type"],
            "BOS",
        )

        self.assertEqual(
            result["setup_priority"],
            "secondary",
        )

        self.assertTrue(
            result["qualified"]
        )

    def test_bearish_choch_is_primary_setup(self):
        structure = self._structure(
            "bearish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bearish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "SELL",
            },
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertEqual(
            result["setup_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["setup_priority"],
            "primary",
        )

        self.assertTrue(
            result["qualified"]
        )

    def test_bearish_bos_is_secondary_setup(self):
        structure = self._structure(
            "bearish",
            [
                self._event(
                    10,
                    "BOS",
                    "bearish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "SELL",
            },
        )

        self.assertEqual(
            result["setup_type"],
            "BOS",
        )

        self.assertEqual(
            result["setup_priority"],
            "secondary",
        )

        self.assertTrue(
            result["qualified"]
        )

    def test_opposite_structure_is_not_qualified(self):
        structure = self._structure(
            "bearish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bearish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["alignment"],
            "not_aligned",
        )

        self.assertIsNone(
            result["setup_type"]
        )

        self.assertFalse(
            result["qualified"]
        )

    def test_wait_htf_direction_does_not_qualify_setup(self):
        structure = self._structure(
            "bullish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bullish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "WAIT",
            },
        )

        self.assertEqual(
            result["alignment"],
            "not_aligned",
        )

        self.assertIsNone(
            result["setup_type"]
        )

        self.assertFalse(
            result["qualified"]
        )

    def test_no_structure_event_waits(self):
        structure = self._structure(
            "bullish",
            [],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertIsNone(
            result["setup_type"]
        )

        self.assertIsNone(
            result["setup_priority"]
        )

        self.assertFalse(
            result["qualified"]
        )

    def test_choch_has_priority_when_both_events_exist(self):
        structure = self._structure(
            "bullish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bullish",
                ),
                self._event(
                    15,
                    "BOS",
                    "bullish",
                ),
            ],
        )

        service = FifteenMinuteSetupService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            higher_timeframe_context={
                "preferred_direction": "BUY",
            },
        )

        self.assertEqual(
            result["setup_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["setup_priority"],
            "primary",
        )

        self.assertTrue(
            result["qualified"]
        )


if __name__ == "__main__":
    unittest.main()