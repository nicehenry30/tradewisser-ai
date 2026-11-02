from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CurrencyFundamentalSnapshot:
    """
    Fundamental condition of one currency.

    This is evidence, not a trading instruction.
    """

    currency: str

    inflation_bias: str = "neutral"
    growth_bias: str = "neutral"
    employment_bias: str = "neutral"
    monetary_policy_bias: str = "neutral"
    interest_rate_bias: str = "neutral"
    economic_surprise_bias: str = "neutral"

    confidence: float = 0.0
    key_drivers: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "inflation_bias": self.inflation_bias,
            "growth_bias": self.growth_bias,
            "employment_bias": self.employment_bias,
            "monetary_policy_bias": self.monetary_policy_bias,
            "interest_rate_bias": self.interest_rate_bias,
            "economic_surprise_bias": self.economic_surprise_bias,
            "confidence": self.confidence,
            "key_drivers": self.key_drivers,
            "risks": self.risks,
        }


@dataclass(frozen=True)
class FundamentalAnalysisResult:
    """
    Structured fundamental analysis for a Forex pair.

    This represents macroeconomic evidence and interpretation,
    not a BUY/SELL instruction.
    """

    symbol: str
    base_currency: str
    quote_currency: str

    base_snapshot: CurrencyFundamentalSnapshot
    quote_snapshot: CurrencyFundamentalSnapshot

    fundamental_direction: str = "neutral"
    confidence: float = 0.0

    event_risk: str = "low"
    upcoming_events: list[dict[str, Any]] = field(
        default_factory=list
    )

    key_drivers: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "base_snapshot": self.base_snapshot.to_dict(),
            "quote_snapshot": self.quote_snapshot.to_dict(),
            "fundamental_direction": self.fundamental_direction,
            "confidence": self.confidence,
            "event_risk": self.event_risk,
            "upcoming_events": self.upcoming_events,
            "key_drivers": self.key_drivers,
            "risks": self.risks,
            "summary": self.summary,
        }