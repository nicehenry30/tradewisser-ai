from app.models.fundamental_analysis import (
    CurrencyFundamentalSnapshot,
)
from app.services.fundamental_analysis_service import (
    FundamentalAnalysisService,
)
from app.fundamental.mock_economic_data_provider import (
    MockEconomicDataProvider,
)


def test_service_analyzes_currency_snapshots():
    service = FundamentalAnalysisService()

    result = service.analyze(
        symbol="EURUSD",
        base_snapshot=CurrencyFundamentalSnapshot(
            currency="EUR",
            growth_bias="bullish",
            monetary_policy_bias="bullish",
            interest_rate_bias="bullish",
            confidence=0.8,
        ),
        quote_snapshot=CurrencyFundamentalSnapshot(
            currency="USD",
            growth_bias="bearish",
            monetary_policy_bias="bearish",
            interest_rate_bias="bearish",
            confidence=0.7,
        ),
    )

    assert result.symbol == "EURUSD"
    assert result.base_currency == "EUR"
    assert result.quote_currency == "USD"
    assert result.fundamental_direction == "bullish"


def test_service_can_analyze_from_dict():
    service = FundamentalAnalysisService()

    result = service.analyze_from_dict(
        symbol="GBPUSD",
        base_data={
            "currency": "GBP",
            "growth_bias": "bullish",
            "interest_rate_bias": "bullish",
            "confidence": 0.8,
            "key_drivers": [
                "Strong UK economic data"
            ],
        },
        quote_data={
            "currency": "USD",
            "growth_bias": "bearish",
            "interest_rate_bias": "bearish",
            "confidence": 0.7,
        },
    )

    assert result.symbol == "GBPUSD"
    assert result.base_currency == "GBP"
    assert result.quote_currency == "USD"
    assert result.fundamental_direction == "bullish"


def test_service_preserves_upcoming_events():
    service = FundamentalAnalysisService()

    events = [
        {
            "name": "US CPI",
            "importance": "high",
        }
    ]

    result = service.analyze_from_dict(
        symbol="EURUSD",
        base_data={
            "currency": "EUR",
            "confidence": 0.7,
        },
        quote_data={
            "currency": "USD",
            "confidence": 0.7,
        },
        upcoming_events=events,
    )

    assert result.upcoming_events == events
    assert result.event_risk == "high"


def test_service_serializes_result():
    service = FundamentalAnalysisService()

    result = service.analyze_from_dict(
        symbol="USDJPY",
        base_data={
            "currency": "USD",
            "interest_rate_bias": "bullish",
            "confidence": 0.8,
        },
        quote_data={
            "currency": "JPY",
            "interest_rate_bias": "bearish",
            "confidence": 0.7,
        },
    )

    data = service.to_dict(result)

    assert data["symbol"] == "USDJPY"
    assert data["base_currency"] == "USD"
    assert data["quote_currency"] == "JPY"
    assert "summary" in data
    assert "base_snapshot" in data
    assert "quote_snapshot" in data

def test_service_can_analyze_from_provider():
    provider = MockEconomicDataProvider(
        currency_data={
            "EUR": {
                "currency": "EUR",
                "growth_bias": "bullish",
                "monetary_policy_bias": "bullish",
                "interest_rate_bias": "bullish",
                "confidence": 0.85,
            },
            "USD": {
                "currency": "USD",
                "growth_bias": "bearish",
                "monetary_policy_bias": "bearish",
                "interest_rate_bias": "bearish",
                "confidence": 0.75,
            },
        },
        upcoming_events=[
            {
                "currency": "USD",
                "name": "CPI",
                "importance": "high",
            }
        ],
    )

    service = FundamentalAnalysisService(
        provider=provider
    )

    result = service.analyze_from_provider("EURUSD")

    assert result.symbol == "EURUSD"
    assert result.base_currency == "EUR"
    assert result.quote_currency == "USD"
    assert result.fundamental_direction == "bullish"
    assert result.event_risk == "high"
    assert len(result.upcoming_events) == 1


def test_provider_analysis_uses_default_provider():
    service = FundamentalAnalysisService()

    assert service.provider is not None
    assert service.provider.__class__.__name__ == "ShowMyTradesEconomicDataProvider"

def test_provider_analysis_rejects_invalid_symbol():
    provider = MockEconomicDataProvider()

    service = FundamentalAnalysisService(
        provider=provider
    )

    try:
        service.analyze_from_provider("EUR")
        assert False
    except ValueError as error:
        assert "six characters" in str(error)