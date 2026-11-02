import pytest

from app.quantitative.historical_comparison import (
    HistoricalConditionComparison,
)


def make_historical_observations():
    return [
        {
            "rsi": 58.0,
            "volatility": 0.20,
            "price_vs_ema20": 0.005,
            "forward_return": 0.010,
            "favorable_move": 0.015,
            "adverse_move": -0.004,
        },
        {
            "rsi": 60.0,
            "volatility": 0.22,
            "price_vs_ema20": 0.007,
            "forward_return": 0.008,
            "favorable_move": 0.012,
            "adverse_move": -0.003,
        },
        {
            "rsi": 70.0,
            "volatility": 0.60,
            "price_vs_ema20": -0.020,
            "forward_return": -0.010,
            "favorable_move": 0.003,
            "adverse_move": -0.014,
        },
    ]


def test_similar_conditions_are_selected():
    comparison = HistoricalConditionComparison()

    result = comparison.compare(
        current={
            "rsi": 59.0,
            "volatility": 0.21,
            "price_vs_ema20": 0.006,
        },
        historical=make_historical_observations(),
    )

    assert result["matching"]["matches"] == 2
    assert result["evidence"]["sample_size"] == 2


def test_matching_outcomes_are_measured():
    comparison = HistoricalConditionComparison()

    result = comparison.compare(
        current={
            "rsi": 59.0,
            "volatility": 0.21,
            "price_vs_ema20": 0.006,
        },
        historical=make_historical_observations(),
    )

    outcomes = result["outcomes"]

    assert outcomes["positive_rate"] == 1.0
    assert outcomes["negative_rate"] == 0.0
    assert outcomes["average_forward_return"] == pytest.approx(
        0.009
    )
    assert outcomes["median_forward_return"] == pytest.approx(
        0.009
    )


def test_no_similar_conditions_returns_insufficient_evidence():
    comparison = HistoricalConditionComparison()

    result = comparison.compare(
        current={
            "rsi": 40.0,
            "volatility": 0.90,
            "price_vs_ema20": -0.05,
        },
        historical=make_historical_observations(),
    )

    assert result["matching"]["matches"] == 0
    assert result["evidence"]["sample_size"] == 0
    assert result["evidence"]["strength"] == "insufficient"
    assert result["outcomes"]["positive_rate"] is None


def test_empty_history_is_rejected():
    comparison = HistoricalConditionComparison()

    with pytest.raises(ValueError):
        comparison.compare(
            current={
                "rsi": 50.0,
                "volatility": 0.20,
                "price_vs_ema20": 0.0,
            },
            historical=[],
        )