from unittest.mock import Mock, patch

import pytest

from app.services.twelve_data_provider import TwelveDataProvider


def test_get_price_returns_normalized_price():
    provider = TwelveDataProvider.__new__(TwelveDataProvider)
    provider.api_key = "test-api-key"

    response = Mock()
    response.json.return_value = {
        "symbol": "XAU/USD",
        "price": "4215.50",
    }

    with patch(
        "app.services.twelve_data_provider.requests.get",
        return_value=response,
    ) as mock_get:
        result = provider.get_price(" xau/usd ")

    assert result == {
        "symbol": "XAU/USD",
        "price": 4215.50,
    }

    mock_get.assert_called_once()


def test_get_candles_returns_normalized_candles():
    provider = TwelveDataProvider.__new__(TwelveDataProvider)
    provider.api_key = "test-api-key"

    response = Mock()
    response.json.return_value = {
        "values": [
            {
                "datetime": "2026-11-01 10:00:00",
                "open": "4200",
                "high": "4220",
                "low": "4190",
                "close": "4210",
                "volume": "100",
            }
        ]
    }

    with patch(
        "app.services.twelve_data_provider.requests.get",
        return_value=response,
    ):
        result = provider.get_candles(
            "XAU/USD",
            interval="1h",
            outputsize=1,
        )

    assert result["symbol"] == "XAU/USD"
    assert result["interval"] == "1h"
    assert result["candles"][0]["open"] == 4200.0
    assert result["candles"][0]["high"] == 4220.0
    assert result["candles"][0]["low"] == 4190.0
    assert result["candles"][0]["close"] == 4210.0
    assert result["candles"][0]["volume"] == 100.0


def test_get_candles_rejects_empty_symbol():
    provider = TwelveDataProvider.__new__(TwelveDataProvider)
    provider.api_key = "test-api-key"

    with pytest.raises(
        ValueError,
        match="Symbol must not be empty",
    ):
        provider.get_candles("")


def test_get_candles_rejects_invalid_outputsize():
    provider = TwelveDataProvider.__new__(TwelveDataProvider)
    provider.api_key = "test-api-key"

    with pytest.raises(
        ValueError,
        match="Output size must be greater than zero",
    ):
        provider.get_candles(
            "XAU/USD",
            outputsize=0,
        )


def test_get_candles_raises_clear_rate_limit_error():
    provider = TwelveDataProvider.__new__(TwelveDataProvider)
    provider.api_key = "test-api-key"

    response = Mock()
    response.status_code = 429

    import requests

    response.raise_for_status.side_effect = requests.HTTPError(
        "429 Client Error: Too Many Requests"
    )

    with patch(
        "app.services.twelve_data_provider.requests.get",
        return_value=response,
    ):
        with pytest.raises(
            RuntimeError,
            match="Twelve Data rate limit exceeded",
        ):
            provider.get_candles(
                "XAU/USD",
                interval="4h",
                outputsize=100,
            )