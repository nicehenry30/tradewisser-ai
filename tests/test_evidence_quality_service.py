from app.models.evidence import EvidenceSource
from app.services.evidence_quality_service import EvidenceQualityService


def test_strong_high_confidence_evidence_is_strong():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="market_regime",
        direction="bullish",
        confidence=0.90,
        sample_size=100,
        strength="strong",
    )

    result = service.evaluate(evidence)

    assert result.quality == "strong"


def test_moderate_evidence_is_moderate():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="market_analysis",
        direction="bullish",
        confidence=0.65,
        sample_size=60,
        strength="moderate",
    )

    result = service.evaluate(evidence)

    assert result.quality == "moderate"


def test_weak_strength_produces_weak_quality():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        confidence=0.80,
        sample_size=100,
        strength="weak",
    )

    result = service.evaluate(evidence)

    assert result.quality == "weak"


def test_low_confidence_produces_weak_quality():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        confidence=0.30,
        sample_size=100,
        strength="strong",
    )

    result = service.evaluate(evidence)

    assert result.quality == "weak"


def test_small_sample_produces_weak_quality():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        confidence=0.90,
        sample_size=20,
        strength="strong",
    )

    result = service.evaluate(evidence)

    assert result.quality == "weak"


def test_neutral_evidence_is_neutral():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="higher_timeframe_context",
        direction="neutral",
        confidence=0.80,
        sample_size=100,
        strength="strong",
    )

    result = service.evaluate(evidence)

    assert result.quality == "neutral"


def test_quality_reasons_explain_the_evaluation():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        confidence=0.85,
        sample_size=120,
        strength="strong",
        limitations=["Historical behavior is not a guarantee."],
    )

    result = service.evaluate(evidence)

    assert result.quality == "strong"
    assert any("strong directional strength" in reason.lower()
               for reason in result.reasons)
    assert any("high" in reason.lower()
               for reason in result.reasons)
    assert any("substantial" in reason.lower()
               for reason in result.reasons)
    assert any("limitations" in reason.lower()
               for reason in result.reasons)

def test_missing_quality_metadata_is_unspecified():
    service = EvidenceQualityService()

    evidence = EvidenceSource(
        source="market_analysis",
        direction="bullish",
    )

    result = service.evaluate(evidence)

    assert result.quality == "unspecified"