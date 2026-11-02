from app.models.evidence import EvidenceSource
from app.services.opportunity_synthesis_service import (
    OpportunitySynthesisService,
)


def make_evidence(
    market_analysis="bullish",
    market_regime="bullish",
    quantitative="bullish",
    higher_timeframe="bullish",
    fundamental=None,
    market_analysis_strength=None,
    market_analysis_confidence=None,
    market_analysis_sample_size=None,
    market_regime_strength=None,
    market_regime_confidence=None,
    market_regime_sample_size=None,
    quantitative_strength=None,
    quantitative_confidence=None,
    quantitative_sample_size=None,
    higher_timeframe_strength=None,
    higher_timeframe_confidence=None,
    higher_timeframe_sample_size=None,
):
    evidence = {
        "market_analysis": EvidenceSource(
            source="market_analysis",
            direction=market_analysis,
            strength=market_analysis_strength,
            confidence=market_analysis_confidence,
            sample_size=market_analysis_sample_size,
        ),
        "market_regime": EvidenceSource(
            source="market_regime",
            direction=market_regime,
            strength=market_regime_strength,
            confidence=market_regime_confidence,
            sample_size=market_regime_sample_size,
        ),
        "quantitative_analytics": EvidenceSource(
            source="quantitative_analytics",
            direction=quantitative,
            strength=quantitative_strength,
            confidence=quantitative_confidence,
            sample_size=quantitative_sample_size,
        ),
        "higher_timeframe_context": EvidenceSource(
            source="higher_timeframe_context",
            direction=higher_timeframe,
            strength=higher_timeframe_strength,
            confidence=higher_timeframe_confidence,
            sample_size=higher_timeframe_sample_size,
        ),
    }

    if fundamental is not None:
        evidence["fundamental_analysis"] = EvidenceSource(
            source="fundamental_analysis",
            direction=fundamental,
        )

    return evidence


def test_all_bullish_evidence_produces_high_quality_long_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence()
    )

    assert result.direction == "LONG"
    assert result.opportunity == "HIGH_QUALITY"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert result.supporting_sources == [
        "market_analysis",
        "market_regime",
        "quantitative_analytics",
        "higher_timeframe_context",
    ]

    assert result.conflicting_sources == []


def test_all_bearish_evidence_produces_high_quality_short_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="bearish",
            market_regime="bearish",
            quantitative="bearish",
            higher_timeframe="bearish",
        )
    )

    assert result.direction == "SHORT"
    assert result.opportunity == "HIGH_QUALITY"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert result.supporting_sources == [
        "market_analysis",
        "market_regime",
        "quantitative_analytics",
        "higher_timeframe_context",
    ]

    assert result.conflicting_sources == []


def test_bullish_majority_produces_valid_long_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            quantitative="neutral",
        )
    )

    assert result.direction == "LONG"
    assert result.opportunity == "VALID"
    assert result.agreement == "STRONG"
    assert result.proceed_to_entry is True

    assert "quantitative_analytics" not in result.supporting_sources
    assert result.conflicting_sources == []


def test_bearish_majority_produces_valid_short_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="bearish",
            market_regime="bearish",
            quantitative="neutral",
            higher_timeframe="bearish",
        )
    )

    assert result.direction == "SHORT"
    assert result.opportunity == "VALID"
    assert result.agreement == "STRONG"
    assert result.proceed_to_entry is True


def test_conflicting_directional_evidence_does_not_proceed_to_entry():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="bullish",
            market_regime="bearish",
            quantitative="bullish",
            higher_timeframe="bearish",
        )
    )

    assert result.direction == "NEUTRAL"
    assert result.opportunity == "NO_OPPORTUNITY"
    assert result.agreement == "CONFLICTED"
    assert result.proceed_to_entry is False


def test_all_neutral_evidence_produces_no_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="neutral",
            market_regime="neutral",
            quantitative="neutral",
            higher_timeframe="neutral",
        )
    )

    assert result.direction == "NEUTRAL"
    assert result.opportunity == "NO_OPPORTUNITY"
    assert result.agreement == "NONE"
    assert result.proceed_to_entry is False


def test_single_directional_source_is_weak_and_does_not_proceed():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="bullish",
            market_regime="neutral",
            quantitative="neutral",
            higher_timeframe="neutral",
        )
    )

    assert result.direction == "LONG"
    assert result.opportunity == "NO_OPPORTUNITY"
    assert result.agreement == "WEAK"
    assert result.proceed_to_entry is False


def test_missing_evidence_source_is_reported_as_limitation():
    service = OpportunitySynthesisService()

    evidence = make_evidence()

    del evidence["quantitative_analytics"]

    result = service.synthesize(evidence)

    assert result.direction == "LONG"
    assert result.proceed_to_entry is True

    assert any(
        "does not contain all four" in limitation
        for limitation in result.limitations
    )


def test_to_dict_serializes_assessment():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence()
    )

    serialized = result.to_dict()

    assert serialized["direction"] == "LONG"
    assert serialized["opportunity"] == "HIGH_QUALITY"
    assert serialized["agreement"] == "HIGH"
    assert serialized["proceed_to_entry"] is True
    assert "supporting_sources" in serialized
    assert "conflicting_sources" in serialized
    assert "limitations" in serialized


def test_bullish_fundamentals_support_high_quality_long_opportunity():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            fundamental="bullish",
        )
    )

    assert result.direction == "LONG"
    assert result.opportunity == "HIGH_QUALITY"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert result.supporting_sources == [
        "market_analysis",
        "market_regime",
        "quantitative_analytics",
        "higher_timeframe_context",
        "fundamental_analysis",
    ]

    assert result.conflicting_sources == []


def test_bearish_fundamentals_conflict_with_long_market_evidence():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            fundamental="bearish",
        )
    )

    assert result.direction == "LONG"
    assert result.opportunity == "VALID"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert "fundamental_analysis" not in result.supporting_sources
    assert "fundamental_analysis" in result.conflicting_sources

    assert any(
        "Fundamental Analysis conflicts" in limitation
        for limitation in result.limitations
    )


def test_bullish_fundamentals_conflict_with_short_market_evidence():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            market_analysis="bearish",
            market_regime="bearish",
            quantitative="bearish",
            higher_timeframe="bearish",
            fundamental="bullish",
        )
    )

    assert result.direction == "SHORT"
    assert result.opportunity == "VALID"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert "fundamental_analysis" not in result.supporting_sources
    assert "fundamental_analysis" in result.conflicting_sources

    assert any(
        "Fundamental Analysis conflicts" in limitation
        for limitation in result.limitations
    )


def test_neutral_fundamentals_reduce_high_quality_to_valid():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence(
            fundamental="neutral",
        )
    )

    assert result.direction == "LONG"
    assert result.opportunity == "VALID"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert "fundamental_analysis" not in result.supporting_sources
    assert "fundamental_analysis" not in result.conflicting_sources

    assert any(
        "Fundamental Analysis is neutral" in limitation
        for limitation in result.limitations
    )


def test_fundamental_analysis_alone_cannot_create_opportunity():
    service = OpportunitySynthesisService()

    evidence = {
        "fundamental_analysis": EvidenceSource(
            source="fundamental_analysis",
            direction="bullish",
        )
    }

    result = service.synthesize(evidence)

    assert result.direction == "NEUTRAL"
    assert result.opportunity == "NO_OPPORTUNITY"
    assert result.proceed_to_entry is False

    assert result.supporting_sources == []
    assert result.conflicting_sources == []

    assert any(
        "all four core market-level evidence sources" in limitation
        for limitation in result.limitations
    )


def test_missing_fundamental_analysis_preserves_existing_behavior():
    service = OpportunitySynthesisService()

    result = service.synthesize(
        make_evidence()
    )

    assert result.direction == "LONG"
    assert result.opportunity == "HIGH_QUALITY"
    assert result.agreement == "HIGH"
    assert result.proceed_to_entry is True

    assert "fundamental_analysis" not in result.supporting_sources
    assert "fundamental_analysis" not in result.conflicting_sources

    assert any(
        "Fundamental Analysis is not available" in limitation
        for limitation in result.limitations
    )

def test_weak_quantitative_evidence_is_explicitly_detected():
    service = OpportunitySynthesisService()

    evidence = make_evidence(
        market_analysis="neutral",
        market_regime="neutral",
        quantitative="bullish",
        quantitative_strength="weak",
        quantitative_confidence=0.45,
        quantitative_sample_size=20,
        higher_timeframe="neutral",
    )

    assessment = service.synthesize(evidence)

    assert assessment.direction == "NEUTRAL"
    assert assessment.opportunity == "NO_OPPORTUNITY"
    assert assessment.proceed_to_entry is False

def test_neutral_higher_timeframe_context_is_explicitly_detected():
    service = OpportunitySynthesisService()

    evidence = make_evidence(
        higher_timeframe="neutral",
    )

    assessment = service.synthesize(evidence)

    assert assessment.direction == "LONG"
    assert assessment.agreement == "STRONG"


def test_strong_market_regime_supports_bullish_opportunity():
    service = OpportunitySynthesisService()

    evidence = make_evidence(
        market_regime="bullish",
        market_regime_strength="strong",
        market_regime_confidence=0.90,
        market_regime_sample_size=100,
    )

    assessment = service.synthesize(evidence)

    assert assessment.direction == "LONG"
    assert assessment.opportunity == "HIGH_QUALITY"

def test_weak_quantitative_evidence_does_not_count_as_full_directional_support():
    service = OpportunitySynthesisService()

    evidence = make_evidence(
        market_analysis="bullish",
        market_analysis_strength="strong",
        market_analysis_confidence=0.90,
        market_analysis_sample_size=100,

        market_regime="bullish",
        market_regime_strength="strong",
        market_regime_confidence=0.90,
        market_regime_sample_size=100,

        quantitative="bullish",
        quantitative_strength="weak",
        quantitative_confidence=0.45,
        quantitative_sample_size=20,

        higher_timeframe="neutral",
    )

    assessment = service.synthesize(evidence)

    assert assessment.direction == "LONG"
    assert assessment.agreement == "MODERATE"
    assert assessment.opportunity == "POTENTIAL"
    assert assessment.proceed_to_entry is False