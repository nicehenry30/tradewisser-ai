from app.fundamental.mock_economic_data_provider import (
    MockEconomicDataProvider,
)


def test_get_currency_data():
    provider = MockEconomicDataProvider(
        currency_data={
            "USD": {
                "currency": "USD",
                "interest_rate": 4.5,
                "inflation": 3.1,
            }
        }
    )

    result = provider.get_currency_data("usd")

    assert result["currency"] == "USD"
    assert result["interest_rate"] == 4.5
    assert result["inflation"] == 3.1


def test_unknown_currency_returns_basic_record():
    provider = MockEconomicDataProvider()

    result = provider.get_currency_data("EUR")

    assert result == {
        "currency": "EUR",
    }


def test_get_upcoming_events_filters_currencies():
    provider = MockEconomicDataProvider(
        upcoming_events=[
            {
                "currency": "USD",
                "name": "CPI",
                "importance": "high",
            },
            {
                "currency": "EUR",
                "name": "ECB Rate Decision",
                "importance": "high",
            },
            {
                "currency": "GBP",
                "name": "GDP",
                "importance": "medium",
            },
        ]
    )

    result = provider.get_upcoming_events(
        ["USD", "EUR"]
    )

    assert len(result) == 2
    assert result[0]["name"] == "CPI"
    assert result[1]["name"] == "ECB Rate Decision"


def test_get_historical_data_respects_limit():
    provider = MockEconomicDataProvider(
        historical_data={
            ("USD", "CPI"): [
                {"date": "2026-01", "value": 3.0},
                {"date": "2026-02", "value": 3.1},
                {"date": "2026-03", "value": 3.2},
            ]
        }
    )

    result = provider.get_historical_data(
        "USD",
        "CPI",
        limit=2,
    )

    assert len(result) == 2
    assert result[0]["value"] == 3.0
    assert result[1]["value"] == 3.1


def test_provider_is_case_insensitive_for_currency():
    provider = MockEconomicDataProvider(
        currency_data={
            "JPY": {
                "currency": "JPY",
                "interest_rate": 0.5,
            }
        }
    )

    result = provider.get_currency_data("jpy")

    assert result["currency"] == "JPY"