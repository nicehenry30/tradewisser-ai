from __future__ import annotations

from typing import Any

from app.fundamental.economic_data_provider import EconomicDataProvider
from app.fundamental.fundamental_engine import FundamentalAnalysisEngine
from app.fundamental.showmytrades_economic_data_provider import (
    ShowMyTradesEconomicDataProvider,
)
from app.models.fundamental_analysis import (
    CurrencyFundamentalSnapshot,
    FundamentalAnalysisResult,
)

class FundamentalAnalysisService:
    """
    Service layer for Forex fundamental analysis.

    Coordinates economic data providers with the deterministic
    fundamental analysis engine.

    It produces fundamental evidence, not BUY/SELL instructions.
    """

    def __init__(
        self,
        engine: FundamentalAnalysisEngine | None = None,
        provider: EconomicDataProvider | None = None,
    ):
        self.engine = engine or FundamentalAnalysisEngine()
        self.provider = provider or ShowMyTradesEconomicDataProvider()


    def analyze(
        self,
        symbol: str,
        base_snapshot: CurrencyFundamentalSnapshot,
        quote_snapshot: CurrencyFundamentalSnapshot,
        upcoming_events: list[dict[str, Any]] | None = None,
    ) -> FundamentalAnalysisResult:
        return self.engine.analyze(
            symbol=symbol,
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            upcoming_events=upcoming_events,
        )

    def analyze_from_provider(
        self,
        symbol: str,
    ) -> FundamentalAnalysisResult:
        """
        Retrieve base/quote currency data from the configured
        economic-data provider and run fundamental analysis.
        """

        if self.provider is None:
            raise ValueError(
                "An EconomicDataProvider is required "
                "for provider-based analysis."
            )

        normalized_symbol = symbol.upper().strip()

        if len(normalized_symbol) != 6:
            raise ValueError(
                "Forex symbol must contain exactly "
                "six characters, for example EURUSD."
            )

        base_currency = normalized_symbol[:3]
        quote_currency = normalized_symbol[3:]

        base_data = self.provider.get_currency_data(
            base_currency
        )

        quote_data = self.provider.get_currency_data(
            quote_currency
        )

        events = self.provider.get_upcoming_events(
            [base_currency, quote_currency]
        )

        return self.analyze_from_dict(
            symbol=normalized_symbol,
            base_data=base_data,
            quote_data=quote_data,
            upcoming_events=events,
        )

    def analyze_from_dict(
        self,
        symbol: str,
        base_data: dict[str, Any],
        quote_data: dict[str, Any],
        upcoming_events: list[dict[str, Any]] | None = None,
    ) -> FundamentalAnalysisResult:

        base_snapshot = CurrencyFundamentalSnapshot(
            currency=str(
                base_data.get("currency", "")
            ).upper(),
            inflation_bias=base_data.get(
                "inflation_bias",
                "neutral",
            ),
            growth_bias=base_data.get(
                "growth_bias",
                "neutral",
            ),
            employment_bias=base_data.get(
                "employment_bias",
                "neutral",
            ),
            monetary_policy_bias=base_data.get(
                "monetary_policy_bias",
                "neutral",
            ),
            interest_rate_bias=base_data.get(
                "interest_rate_bias",
                "neutral",
            ),
            economic_surprise_bias=base_data.get(
                "economic_surprise_bias",
                "neutral",
            ),
            confidence=float(
                base_data.get("confidence", 0.0)
            ),
            key_drivers=list(
                base_data.get("key_drivers", [])
            ),
            risks=list(
                base_data.get("risks", [])
            ),
        )

        quote_snapshot = CurrencyFundamentalSnapshot(
            currency=str(
                quote_data.get("currency", "")
            ).upper(),
            inflation_bias=quote_data.get(
                "inflation_bias",
                "neutral",
            ),
            growth_bias=quote_data.get(
                "growth_bias",
                "neutral",
            ),
            employment_bias=quote_data.get(
                "employment_bias",
                "neutral",
            ),
            monetary_policy_bias=quote_data.get(
                "monetary_policy_bias",
                "neutral",
            ),
            interest_rate_bias=quote_data.get(
                "interest_rate_bias",
                "neutral",
            ),
            economic_surprise_bias=quote_data.get(
                "economic_surprise_bias",
                "neutral",
            ),
            confidence=float(
                quote_data.get("confidence", 0.0)
            ),
            key_drivers=list(
                quote_data.get("key_drivers", [])
            ),
            risks=list(
                quote_data.get("risks", [])
            ),
        )

        return self.analyze(
            symbol=symbol,
            base_snapshot=base_snapshot,
            quote_snapshot=quote_snapshot,
            upcoming_events=upcoming_events,
        )

    @staticmethod
    def to_dict(
        result: FundamentalAnalysisResult,
    ) -> dict[str, Any]:
        return result.to_dict()