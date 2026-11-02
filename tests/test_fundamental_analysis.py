import unittest

from app.fundamental.fundamental_engine import (
    FundamentalAnalysisEngine,
)
from app.models.fundamental_analysis import (
    CurrencyFundamentalSnapshot,
)


class TestFundamentalAnalysisEngine(unittest.TestCase):

    def setUp(self):
        self.engine = FundamentalAnalysisEngine()

    @staticmethod
    def _snapshot(
        currency,
        inflation="neutral",
        growth="neutral",
        employment="neutral",
        monetary_policy="neutral",
        interest_rate="neutral",
        economic_surprise="neutral",
        confidence=0.8,
        key_drivers=None,
        risks=None,
    ):
        return CurrencyFundamentalSnapshot(
            currency=currency,
            inflation_bias=inflation,
            growth_bias=growth,
            employment_bias=employment,
            monetary_policy_bias=monetary_policy,
            interest_rate_bias=interest_rate,
            economic_surprise_bias=economic_surprise,
            confidence=confidence,
            key_drivers=key_drivers or [],
            risks=risks or [],
        )

    def test_bullish_base_currency_produces_bullish_pair(self):
        base = self._snapshot(
            "EUR",
            inflation="bullish",
            growth="bullish",
            employment="bullish",
            monetary_policy="bullish",
            interest_rate="bullish",
            economic_surprise="bullish",
        )

        quote = self._snapshot(
            "USD",
            inflation="bearish",
            growth="bearish",
            employment="bearish",
            monetary_policy="bearish",
            interest_rate="bearish",
            economic_surprise="bearish",
        )

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertEqual(
            result.fundamental_direction,
            "bullish",
        )

        self.assertGreater(
            result.confidence,
            0.5,
        )

    def test_bearish_base_currency_produces_bearish_pair(self):
        base = self._snapshot(
            "EUR",
            inflation="bearish",
            growth="bearish",
            employment="bearish",
            monetary_policy="bearish",
            interest_rate="bearish",
            economic_surprise="bearish",
        )

        quote = self._snapshot(
            "USD",
            inflation="bullish",
            growth="bullish",
            employment="bullish",
            monetary_policy="bullish",
            interest_rate="bullish",
            economic_surprise="bullish",
        )

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertEqual(
            result.fundamental_direction,
            "bearish",
        )

    def test_balanced_currencies_produce_neutral_pair(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertEqual(
            result.fundamental_direction,
            "neutral",
        )

    def test_high_impact_event_creates_high_event_risk(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        events = [
            {
                "name": "US CPI",
                "currency": "USD",
                "importance": "high",
            }
        ]

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
            upcoming_events=events,
        )

        self.assertEqual(
            result.event_risk,
            "high",
        )

    def test_medium_impact_event_creates_medium_event_risk(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        events = [
            {
                "name": "Eurozone PMI",
                "currency": "EUR",
                "importance": "medium",
            }
        ]

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
            upcoming_events=events,
        )

        self.assertEqual(
            result.event_risk,
            "medium",
        )

    def test_no_events_creates_low_event_risk(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertEqual(
            result.event_risk,
            "low",
        )

    def test_key_drivers_are_preserved(self):
        base = self._snapshot(
            "EUR",
            key_drivers=[
                "ECB policy is relatively hawkish"
            ],
        )

        quote = self._snapshot(
            "USD",
            key_drivers=[
                "Fed policy is becoming less restrictive"
            ],
        )

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertIn(
            "ECB policy is relatively hawkish",
            result.key_drivers,
        )

        self.assertIn(
            "Fed policy is becoming less restrictive",
            result.key_drivers,
        )

    def test_currency_risks_are_preserved(self):
        base = self._snapshot(
            "EUR",
            risks=[
                "Political uncertainty"
            ],
        )

        quote = self._snapshot(
            "USD",
            risks=[
                "Weak employment data"
            ],
        )

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertIn(
            "Political uncertainty",
            result.risks,
        )

        self.assertIn(
            "Weak employment data",
            result.risks,
        )

    def test_high_event_risk_is_added_to_risks(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        events = [
            {
                "name": "ECB Rate Decision",
                "currency": "EUR",
                "importance": "high",
            }
        ]

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
            upcoming_events=events,
        )

        self.assertTrue(
            any(
                "High-impact economic events"
                in risk
                for risk in result.risks
            )
        )

    def test_summary_is_human_readable(self):
        base = self._snapshot(
            "EUR",
            key_drivers=[
                "ECB policy is supportive"
            ],
        )

        quote = self._snapshot(
            "USD",
            key_drivers=[
                "US growth is slowing"
            ],
        )

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        self.assertIn(
            "EUR/USD",
            result.summary,
        )

        self.assertIn(
            "fundamental analysis",
            result.summary,
        )

        self.assertIn(
            "does not constitute a trading instruction",
            result.summary,
        )

    def test_result_serialization_contains_expected_fields(self):
        base = self._snapshot("EUR")
        quote = self._snapshot("USD")

        result = self.engine.analyze(
            symbol="EUR/USD",
            base_snapshot=base,
            quote_snapshot=quote,
        )

        data = result.to_dict()

        self.assertEqual(
            data["symbol"],
            "EUR/USD",
        )

        self.assertIn(
            "base_snapshot",
            data,
        )

        self.assertIn(
            "quote_snapshot",
            data,
        )

        self.assertIn(
            "fundamental_direction",
            data,
        )

        self.assertIn(
            "event_risk",
            data,
        )

        self.assertIn(
            "summary",
            data,
        )


if __name__ == "__main__":
    unittest.main()