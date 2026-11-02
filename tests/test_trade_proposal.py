import unittest

from app.models.trade_proposal import (
    TakeProfitCandidate,
    TradeProposal,
)


class TestTradeProposal(unittest.TestCase):

    def test_trade_proposal_can_represent_structural_buy(self):
        proposal = TradeProposal(
            symbol="EURUSD",
            direction="BUY",
            setup_family="REVERSAL",
            setup_type="REVERSAL_CHOCH_BOS",
            entry=1.08500,
            stop_loss=1.08220,
            take_profit=1.08900,
            take_profit_candidates=[
                TakeProfitCandidate(
                    price=1.08900,
                    source="15m_structure",
                    basis="next opposing 15m resistance",
                    risk_reward_ratio=1.43,
                ),
                TakeProfitCandidate(
                    price=1.09400,
                    source="4h_structure",
                    basis="4H major resistance",
                    risk_reward_ratio=3.21,
                ),
            ],
            risk_distance=0.00280,
            reward_distance=0.00400,
            risk_reward_ratio=1.43,
            entry_basis="5m confirmed setup price",
            stop_basis="15m protected low with volatility buffer",
            confidence=82.0,
            market_regime="trending_bullish",
            reasons=[
                "15m setup qualified",
                "5m confirmation aligned",
            ],
        )

        self.assertEqual(proposal.direction, "BUY")
        self.assertEqual(proposal.setup_type, "REVERSAL_CHOCH_BOS")
        self.assertEqual(len(proposal.take_profit_candidates), 2)
        self.assertEqual(proposal.take_profit, 1.08900)
        self.assertEqual(proposal.risk_reward_ratio, 1.43)

    def test_wait_proposal_does_not_require_trade_levels(self):
        proposal = TradeProposal(
            symbol="EURUSD",
            direction="WAIT",
            confidence=0,
            warnings=[
                "5m confirmation is not complete",
            ],
        )

        self.assertEqual(proposal.direction, "WAIT")
        self.assertIsNone(proposal.entry)
        self.assertIsNone(proposal.stop_loss)
        self.assertIsNone(proposal.take_profit)
        self.assertEqual(
            proposal.take_profit_candidates,
            [],
        )

    def test_take_profit_candidate_requires_positive_price(self):
        with self.assertRaises(ValueError):
            TakeProfitCandidate(
                price=0,
                source="15m_structure",
                basis="invalid target",
            )

    def test_risk_reward_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            TakeProfitCandidate(
                price=1.09000,
                source="15m_structure",
                basis="test target",
                risk_reward_ratio=-1,
            )


if __name__ == "__main__":
    unittest.main()