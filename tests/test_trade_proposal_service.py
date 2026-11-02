import unittest

from app.services.trade_proposal_service import TradeProposalService


class TestTradeProposalService(unittest.TestCase):

    def setUp(self):
        self.service = TradeProposalService()

    def _setup(
        self,
        direction="bullish",
        qualified=True,
        setup_family="REVERSAL",
        setup_type="REVERSAL_CHOCH_BOS",
    ):
        return {
            "timeframe": "15m",
            "qualified": qualified,
            "direction": direction,
            "setup_family": setup_family,
            "setup_type": setup_type,
            "structure_pattern": (
                ["CHOCH", "BOS"]
                if "CHOCH_BOS" in setup_type
                else ["CHOCH"]
            ),
        }

    def _confirmation(
        self,
        direction="bullish",
        status="CONFIRMED",
        confirmed=True,
    ):
        return {
            "timeframe": "5m",
            "direction": direction,
            "thesis_direction": direction,
            "alignment": "aligned",
            "confirmed": confirmed,
            "status": status,
            "confirmation_state": status,
        }

    def _context(self):
        return {
            "daily_direction": "bullish",
            "four_hour_direction": "bullish",
            "alignment": "bullish",
            "preferred_direction": "BUY",
            "daily_protected_level": 1.0750,
            "four_hour_protected_level": 1.0800,
            "daily_major_support": 1.0740,
            "daily_major_resistance": 1.1000,
            "four_hour_major_support": 1.0800,
            "four_hour_major_resistance": 1.0950,
            "pdh": 1.0900,
            "pdl": 1.0780,
        }

    def test_unconfirmed_5m_returns_wait(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(),
            five_minute_confirmation=self._confirmation(
                status="DEVELOPING",
                confirmed=False,
            ),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertEqual(proposal.direction, "WAIT")
        self.assertIsNone(proposal.entry)
        self.assertIsNone(proposal.stop_loss)
        self.assertIsNone(proposal.take_profit)

    def test_unqualified_15m_setup_returns_wait(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(
                qualified=False,
            ),
            five_minute_confirmation=self._confirmation(),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertEqual(proposal.direction, "WAIT")
        self.assertIsNone(proposal.entry)

    def test_bullish_confirmation_produces_buy_proposal(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(
                direction="bullish",
            ),
            five_minute_confirmation=self._confirmation(
                direction="bullish",
            ),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertEqual(proposal.direction, "BUY")
        self.assertEqual(proposal.entry, 1.0850)
        self.assertEqual(
            proposal.setup_type,
            "REVERSAL_CHOCH_BOS",
        )
        self.assertIsNotNone(proposal.stop_loss)
        self.assertGreater(
            len(proposal.take_profit_candidates),
            0,
        )

    def test_bearish_confirmation_produces_sell_proposal(self):
        context = self._context()
        context.update(
            {
                "daily_direction": "bearish",
                "four_hour_direction": "bearish",
                "alignment": "bearish",
                "preferred_direction": "SELL",
                "daily_protected_level": 1.1000,
                "four_hour_protected_level": 1.0950,
                "daily_major_support": 1.0700,
                "daily_major_resistance": 1.1050,
                "four_hour_major_support": 1.0750,
                "four_hour_major_resistance": 1.0950,
                "pdh": 1.0920,
                "pdl": 1.0780,
            }
        )

        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(
                direction="bearish",
            ),
            five_minute_confirmation=self._confirmation(
                direction="bearish",
            ),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=context,
        )

        self.assertEqual(proposal.direction, "SELL")
        self.assertEqual(proposal.entry, 1.0850)
        self.assertIsNotNone(proposal.stop_loss)
        self.assertGreater(
            len(proposal.take_profit_candidates),
            0,
        )

    def test_opposite_5m_direction_returns_wait(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(
                direction="bullish",
            ),
            five_minute_confirmation=self._confirmation(
                direction="bearish",
            ),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertEqual(proposal.direction, "WAIT")

    def test_buy_stop_loss_is_below_entry(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(),
            five_minute_confirmation=self._confirmation(),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertEqual(proposal.direction, "BUY")
        self.assertLess(
            proposal.stop_loss,
            proposal.entry,
        )

    def test_buy_targets_are_above_entry(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(),
            five_minute_confirmation=self._confirmation(),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        for target in proposal.take_profit_candidates:
            self.assertGreater(
                target.price,
                proposal.entry,
            )

    def test_risk_reward_is_calculated_for_targets(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(),
            five_minute_confirmation=self._confirmation(),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertIsNotNone(
            proposal.risk_distance,
        )

        for target in proposal.take_profit_candidates:
            self.assertIsNotNone(
                target.risk_reward_ratio,
            )
            self.assertGreater(
                target.risk_reward_ratio,
                0,
            )

    def test_service_does_not_calculate_position_size(self):
        proposal = self.service.propose(
            symbol="EURUSD",
            fifteen_minute_setup=self._setup(),
            five_minute_confirmation=self._confirmation(),
            current_price=1.0850,
            market_analysis={
                "atr_14": 0.0010,
            },
            higher_timeframe_context=self._context(),
        )

        self.assertFalse(
            hasattr(proposal, "position_size")
        )