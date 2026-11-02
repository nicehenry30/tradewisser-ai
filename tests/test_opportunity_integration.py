from app.models.evidence import EvidenceSource
from app.services.evidence_service import EvidenceService
from app.services.opportunity_synthesis_service import (
    OpportunitySynthesisService,
)


class StubMarketAnalysisService:
    def analyze(self, candles):
        return {
            "trend": "bullish",
            "market_structure": {
                "direction": "bullish",
                "strength": 2,
            },
            "latest_close": 100.0,
            "ema_20": 99.0,
            "ema_50": 97.0,
            "rsi_14": 60.0,
            "atr_14": 2.0,
            "swing_highs": [],
            "swing_lows": [],
            "structure_events": [],
        }


class StubMarketRegimeService:
    class Result:
        def to_dict(self):
            return {
                "regime": "trending_bullish",
                "confidence": 0.8,
                "reasons": ["higher_analysis_and_structure_are_bullish"],
            }

    def classify(self, analysis):
        return self.Result()


class StubQuantitativeAnalytics:
    def analyze(self, candles, forward_bars=5):
        return {
            "engine": "quantitative_analytics",
            "version": "1.0",
            "sample_size": len(candles),
            "returns": {
                "latest_return": 0.01,
            },
            "volatility": {
                "mean": 0.02,
            },
            "forward_behavior": {
                "positive_rate": 0.7,
                "negative_rate": 0.3,
                "average_forward_return": 0.02,
                "median_forward_return": 0.015,
                "forward_observations": 50,
            },
            "range_behavior": {
                "average_range": 2.0,
            },
        }


class StubHigherTimeframeContextService:
    def analyze(self, daily_candles, four_hour_candles):
        return {
            "daily_direction": "bullish",
            "four_hour_direction": "bullish",
            "alignment": "bullish",
            "preferred_direction": "BUY",
            "daily_protected_level": 95.0,
            "four_hour_protected_level": 98.0,
            "daily_major_support": 94.0,
            "daily_major_resistance": 105.0,
            "four_hour_major_support": 97.0,
            "four_hour_major_resistance": 103.0,
            "pdh": 102.0,
            "pdl": 96.0,
            "reference_date": "2026-10-23",
        }


class StubEvidenceBuilder:
    def build_market_analysis(self, analysis):
        return EvidenceSource(
            source="market_analysis",
            direction="bullish",
        )

    def build_market_regime(self, regime):
        return EvidenceSource(
            source="market_regime",
            direction="bullish",
        )

    def build_quantitative_analysis(self, quantitative):
        return EvidenceSource(
            source="quantitative_analytics",
            direction="bullish",
            sample_size=quantitative["forward_behavior"][
                "forward_observations"
            ],
        )

    def build_higher_timeframe_context(self, context):
        return EvidenceSource(
            source="higher_timeframe_context",
            direction="bullish",
        )


def test_evidence_service_output_can_be_passed_to_opportunity_synthesis():
    evidence_service = EvidenceService(
        market_analysis_service=StubMarketAnalysisService(),
        market_regime_service=StubMarketRegimeService(),
        quantitative_analytics=StubQuantitativeAnalytics(),
        higher_timeframe_context_service=(
            StubHigherTimeframeContextService()
        ),
        evidence_builder=StubEvidenceBuilder(),
    )

    evidence = evidence_service.build_evidence(
        candles=[{"close": 100.0}] * 30,
        daily_candles=[{"high": 105.0, "low": 95.0}] * 2,
        four_hour_candles=[{"high": 103.0, "low": 97.0}] * 2,
    )

    synthesis_service = OpportunitySynthesisService()
    assessment = synthesis_service.synthesize(evidence)

    assert assessment.direction == "LONG"
    assert assessment.opportunity == "HIGH_QUALITY"
    assert assessment.agreement == "HIGH"
    assert assessment.proceed_to_entry is True


def test_evidence_service_can_directly_assess_opportunity():
    evidence_service = EvidenceService(
        market_analysis_service=StubMarketAnalysisService(),
        market_regime_service=StubMarketRegimeService(),
        quantitative_analytics=StubQuantitativeAnalytics(),
        higher_timeframe_context_service=(
            StubHigherTimeframeContextService()
        ),
        evidence_builder=StubEvidenceBuilder(),
    )

    evidence = evidence_service.build_evidence(
        candles=[{"close": 100.0}] * 30,
        daily_candles=[{"high": 105.0, "low": 95.0}] * 2,
        four_hour_candles=[{"high": 103.0, "low": 97.0}] * 2,
    )

    assessment = evidence_service.assess_opportunity(evidence)

    assert assessment.direction == "LONG"
    assert assessment.opportunity == "HIGH_QUALITY"
    assert assessment.agreement == "HIGH"
    assert assessment.proceed_to_entry is True