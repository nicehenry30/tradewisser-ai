from app.fundamental.mock_economic_data_provider import (
    MockEconomicDataProvider,
)
from app.services.evidence_service import EvidenceService
from app.services.fundamental_analysis_service import (
    FundamentalAnalysisService,
)


def make_candles(count=60):
    candles = []

    for index in range(count):
        price = 3000.0 + (index * 2.0)

        candles.append(
            {
                "datetime": f"2026-01-{index + 1:02d}T00:00:00",
                "open": price - 1.0,
                "high": price + 3.0,
                "low": price - 3.0,
                "close": price + 2.0,
                "volume": 1000.0,
            }
        )

    return candles


def test_evidence_service_builds_all_evidence_sources():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
    )

    assert set(evidence.keys()) == {
        "market_analysis",
        "market_regime",
        "quantitative_analytics",
        "higher_timeframe_context",
    }

    assert evidence["market_analysis"].source == "market_analysis"
    assert evidence["market_regime"].source == "market_regime"

    assert (
        evidence["quantitative_analytics"].source
        == "quantitative_analytics"
    )

    assert (
        evidence["higher_timeframe_context"].source
        == "higher_timeframe_context"
    )


def test_evidence_service_preserves_quantitative_sample_size():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
    )

    quantitative = evidence["quantitative_analytics"]

    assert quantitative.sample_size == 55


def test_evidence_service_builds_higher_timeframe_context():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
    )

    higher_timeframe = evidence["higher_timeframe_context"]

    assert higher_timeframe.source == "higher_timeframe_context"

    assert higher_timeframe.direction in {
        "bullish",
        "bearish",
        "neutral",
    }

    observation_names = {
        observation.name
        for observation in higher_timeframe.observations
    }

    assert "daily_direction" in observation_names
    assert "four_hour_direction" in observation_names
    assert "alignment" in observation_names
    assert "preferred_direction" in observation_names
    assert "pdh" in observation_names
    assert "pdl" in observation_names


def test_evidence_service_can_serialize_complete_package():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
    )

    result = service.to_dict(evidence)

    assert "market_analysis" in result
    assert "market_regime" in result
    assert "quantitative_analytics" in result
    assert "higher_timeframe_context" in result

    assert result["market_analysis"]["source"] == "market_analysis"
    assert result["market_regime"]["source"] == "market_regime"

    assert (
        result["quantitative_analytics"]["source"]
        == "quantitative_analytics"
    )

    assert (
        result["higher_timeframe_context"]["source"]
        == "higher_timeframe_context"
    )


def test_evidence_service_does_not_produce_trade_action():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
    )

    serialized = service.to_dict(evidence)

    for source in serialized.values():
        assert "action" not in source
        assert "trade_action" not in source
        assert "buy" not in source
        assert "sell" not in source


def test_evidence_service_builds_fundamental_analysis_when_symbol_is_supplied():
    provider = MockEconomicDataProvider(
        currency_data={
            "EUR": {
                "currency": "EUR",
                "inflation_bias": "bullish",
                "growth_bias": "bullish",
                "employment_bias": "neutral",
                "monetary_policy_bias": "bullish",
                "interest_rate_bias": "bullish",
                "economic_surprise_bias": "bullish",
                "confidence": 0.8,
                "key_drivers": ["ECB policy support"],
                "risks": [],
            },
            "USD": {
                "currency": "USD",
                "inflation_bias": "bearish",
                "growth_bias": "bearish",
                "employment_bias": "neutral",
                "monetary_policy_bias": "bearish",
                "interest_rate_bias": "bearish",
                "economic_surprise_bias": "bearish",
                "confidence": 0.8,
                "key_drivers": ["Fed easing"],
                "risks": [],
            },
        },
        upcoming_events=[
            {
                "currency": "USD",
                "importance": "high",
                "title": "Fed Interest Rate Decision",
            }
        ],
    )

    fundamental_service = FundamentalAnalysisService(
        provider=provider
    )

    service = EvidenceService(
        fundamental_analysis_service=fundamental_service
    )

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
        symbol="EURUSD",
    )

    assert "fundamental_analysis" in evidence

    fundamental = evidence["fundamental_analysis"]

    assert fundamental.source == "fundamental_analysis"
    assert fundamental.direction == "bullish"

    assert fundamental.confidence is not None
    assert fundamental.confidence > 0

    observation_names = {
        observation.name
        for observation in fundamental.observations
    }

    assert "fundamental_direction" in observation_names
    assert "confidence" in observation_names
    assert "event_risk" in observation_names
    assert "base_currency" in observation_names
    assert "quote_currency" in observation_names

def test_evidence_service_uses_real_fundamental_provider_when_symbol_is_supplied():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        forward_bars=5,
        symbol="EURUSD",
    )

    assert "fundamental_analysis" in evidence

    fundamental = evidence["fundamental_analysis"]

    assert fundamental.source == "fundamental_analysis"

    observation_names = {
        observation.name
        for observation in fundamental.observations
    }

    assert "fundamental_direction" in observation_names
    assert "confidence" in observation_names
    assert "event_risk" in observation_names
    assert "base_currency" in observation_names
    assert "quote_currency" in observation_names

    assert any(
        observation.name == "base_currency"
        and observation.value == "EUR"
        for observation in fundamental.observations
    )

    assert any(
        observation.name == "quote_currency"
        and observation.value == "USD"
        for observation in fundamental.observations
    )

def test_evidence_service_builds_multi_timeframe_quantitative_evidence():
    service = EvidenceService()

    candles = make_candles()
    daily_candles = make_candles(10)
    four_hour_candles = make_candles(60)
    one_hour_candles = make_candles(60)

    evidence = service.build_evidence(
        candles=candles,
        daily_candles=daily_candles,
        four_hour_candles=four_hour_candles,
        one_hour_candles=one_hour_candles,
        forward_bars=5,
    )

    quantitative = evidence["quantitative_analytics"]

    assert quantitative.source == "quantitative_analytics"

    assert quantitative.direction in {
        "bullish",
        "bearish",
        "neutral",
    }

    assert quantitative.strength in {
        "strong",
        "moderate",
        "weak",
    }

    assert quantitative.confidence is not None

    assert quantitative.sample_size == 110

    observation_names = {
        observation.name
        for observation in quantitative.observations
    }

    assert "four_hour_direction" in observation_names
    assert "one_hour_direction" in observation_names
    assert "four_hour_strength" in observation_names
    assert "one_hour_strength" in observation_names
    assert "four_hour_forward_positive_rate" in observation_names
    assert "one_hour_forward_positive_rate" in observation_names
    assert "four_hour_volatility" in observation_names
    assert "one_hour_volatility" in observation_names