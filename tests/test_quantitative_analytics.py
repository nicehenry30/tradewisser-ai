from datetime import datetime, timedelta

import pytest

from app.quantitative.analytics import QuantitativeAnalytics


def make_candles(count: int = 60) -> list[dict]:
    candles = []

    price = 100.0
    start = datetime(2026, 1, 1, 0, 0, 0)

    for index in range(count):
        open_price = price
        close_price = price + 1.0

        timestamp = start + timedelta(hours=index)

        candles.append(
            {
                "datetime": timestamp.isoformat(),
                "open": open_price,
                "high": close_price + 0.5,
                "low": open_price - 0.5,
                "close": close_price,
                "volume": 1000.0,
            }
        )

        price = close_price

    return candles


def test_quantitative_analysis_returns_expected_sections():
    analytics = QuantitativeAnalytics()

    result = analytics.analyze(
        make_candles(),
        forward_bars=5,
    )

    assert result["engine"] == "quantitative_analytics"
    assert result["version"] == "1.0"

    assert "sample" in result
    assert "returns" in result
    assert "volatility" in result
    assert "forward_behavior" in result
    assert "range_behavior" in result


def test_positive_market_produces_positive_forward_behavior():
    analytics = QuantitativeAnalytics()

    result = analytics.analyze(
        make_candles(),
        forward_bars=5,
    )

    forward = result["forward_behavior"]

    assert forward["positive_rate"] == 1.0
    assert forward["average_return"] > 0


def test_insufficient_candles_are_rejected():
    analytics = QuantitativeAnalytics()

    with pytest.raises(ValueError):
        analytics.analyze(
            make_candles(10),
            forward_bars=5,
        )


def test_invalid_forward_bars_are_rejected():
    analytics = QuantitativeAnalytics()

    with pytest.raises(ValueError):
        analytics.analyze(
            make_candles(),
            forward_bars=0,
        )