import unittest

from app.services.five_minute_confirmation_service import (
    FiveMinuteConfirmationService,
)


class FakeStructureEngine:
    def __init__(self, result):
        self.result = result
        self.received_candles = None
        self.received_timeframe = None

    def analyze(self, candles, timeframe):
        self.received_candles = candles
        self.received_timeframe = timeframe
        return self.result


class TestFiveMinuteConfirmationService(unittest.TestCase):

    @staticmethod
    def _structure(
        current_direction,
        events,
    ):
        return {
            "timeframe": "5m",
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

    @staticmethod
    def _setup(
        direction="bullish",
        setup_family="REVERSAL",
        setup_type="REVERSAL_CHOCH",
        qualified=True,
    ):
        if "CHOCH_BOS" in setup_type:
            structure_pattern = ["CHOCH", "BOS"]
        elif "CHOCH" in setup_type:
            structure_pattern = ["CHOCH"]
        elif "BOS" in setup_type:
            structure_pattern = ["BOS"]
        else:
            structure_pattern = []

        return {
            "timeframe": "15m",
            "htf_direction": (
                "BUY"
                if direction == "bullish"
                else "SELL"
            ),
            "structure_direction": direction,
            "alignment": "aligned",
            "setup_family": setup_family,
            "setup_type": setup_type,
            "structure_pattern": structure_pattern,
            "trigger": (
                "CHOCH"
                if "CHOCH" in setup_type
                else "BOS"
            ),
            "direction": direction,
            "setup_priority": "primary",
            "qualified": qualified,
            "setup_stage": (
                "READY_FOR_5M_CONFIRMATION"
                if qualified
                else "WAIT"
            ),
            "confirmation_type": "5M_CONFIRMATION",
            "confirmed": False,
        }
    
    def test_same_bullish_choch_pattern_confirms(self):
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

        engine = FakeStructureEngine(structure)

        service = FiveMinuteConfirmationService(
            structure_engine=engine
        )

        result = service.analyze(
            candles=["5m-candle"],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            engine.received_timeframe,
            "5m",
        )

        self.assertEqual(
            result["structure_direction"],
            "bullish",
        )

        self.assertEqual(
            result["setup_family"],
            "REVERSAL",
        )

        self.assertEqual(
            result["setup_type"],
            "REVERSAL_CHOCH",
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_same_bullish_choch_bos_pattern_confirms(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH_BOS",
            ),
        )

        self.assertEqual(
            result["structure_pattern"],
            ["CHOCH", "BOS"],
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH_BOS",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_same_bullish_continuation_bos_confirms(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="CONTINUATION",
                setup_type="TREND_CONTINUATION_BOS",
            ),
        )

        self.assertEqual(
            result["setup_family"],
            "CONTINUATION",
        )

        self.assertEqual(
            result["confirmation_type"],
            "BOS",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_same_bullish_continuation_choch_bos_confirms(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="CONTINUATION",
                setup_type="TREND_CONTINUATION_CHOCH_BOS",
            ),
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH_BOS",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_same_bearish_choch_pattern_confirms(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bearish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            result["structure_direction"],
            "bearish",
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_same_bearish_choch_bos_pattern_confirms(self):
        structure = self._structure(
            "bearish",
            [
                self._event(
                    10,
                    "CHOCH",
                    "bearish",
                ),
                self._event(
                    15,
                    "BOS",
                    "bearish",
                ),
            ],
        )

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bearish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH_BOS",
            ),
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH_BOS",
        )

        self.assertTrue(
            result["confirmed"]
        )

    def test_opposite_5m_direction_does_not_confirm(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            result["alignment"],
            "not_aligned",
        )

        self.assertFalse(
            result["confirmed"]
        )

        self.assertIsNone(
            result["confirmation_type"]
        )

    def test_no_5m_structure_event_waits(self):
        structure = self._structure(
            "bullish",
            [],
        )

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertFalse(
            result["confirmed"]
        )

        self.assertIsNone(
            result["confirmation_type"]
        )

        self.assertEqual(
            result["status"],
            "WAIT",
        )

    def test_unqualified_15m_setup_blocks_5m_confirmation(self):
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

        engine = FakeStructureEngine(structure)

        service = FiveMinuteConfirmationService(
            structure_engine=engine
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
                qualified=False,
            ),
        )

        self.assertFalse(
            result["confirmed"]
        )

        self.assertEqual(
            result["status"],
            "WAIT",
        )

        self.assertIsNone(
            result["confirmation_type"]
        )

    def test_5m_does_not_require_same_pattern_when_valid_confirmation_exists(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertTrue(
            result["confirmed"]
        )

        self.assertEqual(
            result["confirmation_type"],
            "BOS",
        )

    def test_partial_confirmation_is_developing(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH_BOS",
            ),
        )

        self.assertEqual(
            result["thesis_direction"],
            "bullish",
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertFalse(
            result["confirmed"]
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH",
        )

        self.assertEqual(
            result["status"],
            "DEVELOPING",
        )

        self.assertEqual(
            result["confirmation_state"],
            "DEVELOPING",
        )

    def test_confirmed_state_is_explicit(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH_BOS",
            ),
        )

        self.assertEqual(
            result["thesis_direction"],
            "bullish",
        )

        self.assertEqual(
            result["alignment"],
            "aligned",
        )

        self.assertTrue(
            result["confirmed"]
        )

        self.assertEqual(
            result["confirmation_type"],
            "CHOCH_BOS",
        )

        self.assertEqual(
            result["status"],
            "CONFIRMED",
        )

        self.assertEqual(
            result["confirmation_state"],
            "CONFIRMED",
        )

    def test_opposite_direction_remains_wait(self):
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

        service = FiveMinuteConfirmationService(
            structure_engine=FakeStructureEngine(
                structure
            )
        )

        result = service.analyze(
            candles=[],
            fifteen_minute_setup=self._setup(
                direction="bullish",
                setup_family="REVERSAL",
                setup_type="REVERSAL_CHOCH",
            ),
        )

        self.assertEqual(
            result["thesis_direction"],
            "bullish",
        )

        self.assertEqual(
            result["alignment"],
            "not_aligned",
        )

        self.assertFalse(
            result["confirmed"]
        )

        self.assertEqual(
            result["status"],
            "WAIT",
        )

        self.assertEqual(
            result["confirmation_state"],
            "WAIT",
        )
