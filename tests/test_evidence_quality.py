from app.models.evidence_quality import EvidenceQuality


def test_strong_evidence_quality_serializes_correctly():
    quality = EvidenceQuality(
        quality="strong",
        reasons=["Strong directional evidence", "High confidence"],
    )

    result = quality.to_dict()

    assert result == {
        "quality": "strong",
        "reasons": [
            "Strong directional evidence",
            "High confidence",
        ],
    }


def test_moderate_evidence_quality_is_supported():
    quality = EvidenceQuality(
        quality="moderate",
        reasons=["Moderate directional evidence"],
    )

    assert quality.quality == "moderate"


def test_weak_evidence_quality_is_supported():
    quality = EvidenceQuality(
        quality="weak",
        reasons=["Low confidence"],
    )

    assert quality.quality == "weak"


def test_neutral_evidence_quality_is_supported():
    quality = EvidenceQuality(
        quality="neutral",
        reasons=["Evidence is neutral"],
    )

    assert quality.quality == "neutral"


def test_conflicted_evidence_quality_is_supported():
    quality = EvidenceQuality(
        quality="conflicted",
        reasons=["Evidence sources disagree"],
    )

    assert quality.quality == "conflicted"