from app.models.evidence import (
    EvidenceObservation,
    EvidenceSource,
)


def test_observation_serializes_correctly():
    observation = EvidenceObservation(
        name="historical_positive_rate",
        value=0.648,
        unit="probability",
        description="Historical positive forward outcome rate.",
    )

    result = observation.to_dict()

    assert result["name"] == "historical_positive_rate"
    assert result["value"] == 0.648
    assert result["unit"] == "probability"
    assert (
        result["description"]
        == "Historical positive forward outcome rate."
    )


def test_evidence_source_serializes_observations():
    source = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        confidence=0.68,
        sample_size=327,
        strength="moderate",
        observations=[
            EvidenceObservation(
                name="historical_positive_rate",
                value=0.648,
                unit="probability",
            ),
        ],
        limitations=[
            "Historical similarity does not guarantee future outcome."
        ],
    )

    result = source.to_dict()

    assert result["source"] == "quantitative_analytics"
    assert result["direction"] == "bullish"
    assert result["confidence"] == 0.68

    assert result["evidence"]["sample_size"] == 327
    assert result["evidence"]["strength"] == "moderate"

    assert len(result["observations"]) == 1
    assert (
        result["observations"][0]["name"]
        == "historical_positive_rate"
    )

    assert len(result["limitations"]) == 1


def test_default_evidence_is_neutral():
    source = EvidenceSource(
        source="market_analysis",
    )

    result = source.to_dict()

    assert result["direction"] == "neutral"
    assert result["observations"] == []
    assert result["confidence"] is None
    assert result["evidence"]["sample_size"] is None
    assert result["evidence"]["strength"] is None
    assert result["limitations"] == []