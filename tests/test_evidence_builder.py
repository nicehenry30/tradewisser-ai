from app.services.evidence_builder import EvidenceBuilder

from app.models.fundamental_analysis import (
    CurrencyFundamentalSnapshot,
)
from app.fundamental.fundamental_engine import (
    FundamentalAnalysisEngine,
)


def test_market_analysis_is_converted_to_evidence():
    builder = EvidenceBuilder()

    analysis = {
        "trend": "bullish",
        "latest_close": 3350.0,
        "ema_20": 3330.0,
        "ema_50": 3290.0,
        "rsi_14": 61.0,
        "atr_14": 18.0,
        "market_structure": {
            "direction": "bullish",
            "strength": 3,
        },
        "structure_events": [
            {
                "type": "BOS",
                "direction": "bullish",
            }
        ],
    }

    evidence = builder.build_market_analysis(analysis)

    assert evidence.source == "market_analysis"
    assert evidence.direction == "bullish"
    assert len(evidence.observations) == 8


def test_market_regime_is_converted_to_evidence():
    builder = EvidenceBuilder()

    regime = {
        "regime": "trending_bullish",
        "confidence": 0.8,
        "reasons": [
            "higher_analysis_and_structure_are_bullish"
        ],
    }

    evidence = builder.build_market_regime(regime)

    assert evidence.source == "market_regime"
    assert evidence.direction == "bullish"
    assert evidence.confidence == 0.8
    assert len(evidence.observations) == 2


def test_quantitative_analysis_is_converted_to_evidence():
    builder = EvidenceBuilder()

    quantitative = {
        "returns": {
            "latest": 0.002,
        },
        "sample": {
            "forward_observations": 327,
        },
        "forward_behavior": {
            "positive_rate": 0.648,
            "negative_rate": 0.352,
            "average_return": 0.0024,
            "median_return": 0.0018,
        },
        "volatility": {
            "classification": "high",
        },
        "range_behavior": {
            "average_favorable_move": 0.004,
            "average_adverse_move": -0.002,
        },
    }

    evidence = builder.build_quantitative_analysis(quantitative)

    assert evidence.source == "quantitative_analytics"
    assert evidence.direction == "bullish"
    assert evidence.sample_size == 327
    assert len(evidence.observations) == 7


def test_quantitative_analysis_is_neutral_when_outcomes_are_equal():
    builder = EvidenceBuilder()

    quantitative = {
        "returns": {},
        "sample": {
            "forward_observations": 100,
        },
        "forward_behavior": {
            "positive_rate": 0.5,
            "negative_rate": 0.5,
            "average_return": 0.0,
            "median_return": 0.0,
        },
        "volatility": {},
        "range_behavior": {},
    }



    evidence = builder.build_quantitative_analysis(quantitative)

    assert evidence.direction == "neutral"

def test_build_fundamental_analysis():
    builder = EvidenceBuilder()

    engine = FundamentalAnalysisEngine()

    result = engine.analyze(
        symbol="EURUSD",
        base_snapshot=CurrencyFundamentalSnapshot(
            currency="EUR",
            growth_bias="bullish",
            monetary_policy_bias="bullish",
            interest_rate_bias="bullish",
            confidence=0.85,
            key_drivers=[
                "ECB policy remains restrictive"
            ],
        ),
        quote_snapshot=CurrencyFundamentalSnapshot(
            currency="USD",
            growth_bias="bearish",
            monetary_policy_bias="bearish",
            interest_rate_bias="bearish",
            confidence=0.75,
        ),
        upcoming_events=[
            {
                "currency": "USD",
                "name": "CPI",
                "importance": "high",
            }
        ],
    )

    evidence = builder.build_fundamental_analysis(result)

    assert evidence.source == "fundamental_analysis"
    assert evidence.direction == "bullish"
    assert evidence.confidence == result.confidence
    assert evidence.strength == "strong"

    observation_names = {
        observation.name
        for observation in evidence.observations
    }

    assert "fundamental_direction" in observation_names
    assert "event_risk" in observation_names
    assert "summary" in observation_names
    assert "key_drivers" in observation_names
    assert "risks" in observation_names
    assert "upcoming_events" in observation_names

    assert any(
        "High-impact economic events" in limitation
        for limitation in evidence.limitations
    )