from app.models.evidence import EvidenceSource
from app.services.quantitative_evidence_service import (
    QuantitativeEvidenceService,
)


def make_quantitative(
    *,
    positive_rate=0.70,
    negative_rate=0.30,
    average_return=0.01,
    median_return=0.008,
    forward_observations=100,
    volatility_classification="normal",
):
    return {
        "sample": {
            "forward_observations": forward_observations,
        },
        "forward_behavior": {
            "positive_rate": positive_rate,
            "negative_rate": negative_rate,
            "average_return": average_return,
            "median_return": median_return,
        },
        "volatility": {
            "classification": volatility_classification,
        },
        "range_behavior": {
            "average_favorable_move": 0.012,
            "average_adverse_move": -0.004,
        },
        "returns": {
            "latest": 0.003,
        },
    }


def test_aligned_bullish_timeframes_produce_bullish_family():
    service = QuantitativeEvidenceService()

    result = service.synthesize(
        four_hour=make_quantitative(
            positive_rate=0.80,
            negative_rate=0.20,
            average_return=0.02,
        ),
        one_hour=make_quantitative(
            positive_rate=0.70,
            negative_rate=0.30,
            average_return=0.01,
        ),
    )

    assert isinstance(result, EvidenceSource)
    assert result.source == "quantitative_analytics"
    assert result.direction == "bullish"


def test_aligned_bearish_timeframes_produce_bearish_family():
    service = QuantitativeEvidenceService()

    result = service.synthesize(
        four_hour=make_quantitative(
            positive_rate=0.20,
            negative_rate=0.80,
            average_return=-0.02,
        ),
        one_hour=make_quantitative(
            positive_rate=0.30,
            negative_rate=0.70,
            average_return=-0.01,
        ),
    )

    assert result.direction == "bearish"


def test_conflicting_timeframes_reduce_quantitative_family_to_neutral():
    service = QuantitativeEvidenceService()

    result = service.synthesize(
        four_hour=make_quantitative(
            positive_rate=0.80,
            negative_rate=0.20,
            average_return=0.02,
        ),
        one_hour=make_quantitative(
            positive_rate=0.20,
            negative_rate=0.80,
            average_return=-0.02,
        ),
    )

    assert result.direction == "neutral"
    assert result.strength in {"weak", "moderate"}
    assert result.confidence is not None


def test_neutral_one_hour_reduces_confidence_but_preserves_four_hour_direction():
    service = QuantitativeEvidenceService()

    result = service.synthesize(
        four_hour=make_quantitative(
            positive_rate=0.80,
            negative_rate=0.20,
            average_return=0.02,
        ),
        one_hour=make_quantitative(
            positive_rate=0.50,
            negative_rate=0.50,
            average_return=0.0,
            median_return=0.0,
        ),
    )

    assert result.direction == "bullish"
    assert result.confidence is not None
    assert result.confidence < 1.0
