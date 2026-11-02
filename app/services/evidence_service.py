from __future__ import annotations

from typing import Any

from app.models.evidence import EvidenceSource
from app.models.opportunity_assessment import OpportunityAssessment
from app.quantitative.analytics import QuantitativeAnalytics
from app.services.evidence_builder import EvidenceBuilder
from app.services.fundamental_analysis_service import (
    FundamentalAnalysisService,
)
from app.services.higher_timeframe_context_service import (
    HigherTimeframeContextService,
)
from app.services.market_analysis_service import MarketAnalysisService
from app.services.market_regime_service import MarketRegimeService
from app.services.opportunity_synthesis_service import (
    OpportunitySynthesisService,
)
from app.services.quantitative_evidence_service import (
    QuantitativeEvidenceService,
)


class EvidenceService:
    """
    Orchestrates Tradewisser's market analytical engines and converts
    their outputs into the common Evidence Contract.

    Top-level evidence sources:

        - Market Analysis
        - Market Regime
        - Quantitative Analytics
        - Higher-Timeframe Context
        - Fundamental Analysis

    This service does not make trading decisions.

    15M and 5M analysis are intentionally excluded here.
    They belong to the later entry-analysis phase.
    """

    def __init__(
        self,
        market_analysis_service: MarketAnalysisService | None = None,
        market_regime_service: MarketRegimeService | None = None,
        quantitative_analytics: QuantitativeAnalytics | None = None,
        quantitative_evidence_service: (
            QuantitativeEvidenceService | None
        ) = None,
        higher_timeframe_context_service: (
            HigherTimeframeContextService | None
        ) = None,
        fundamental_analysis_service: (
            FundamentalAnalysisService | None
        ) = None,
        evidence_builder: EvidenceBuilder | None = None,
        opportunity_synthesis_service: (
            OpportunitySynthesisService | None
        ) = None,
    ):
        self.market_analysis_service = (
            market_analysis_service or MarketAnalysisService()
        )

        self.market_regime_service = (
            market_regime_service or MarketRegimeService()
        )

        self.quantitative_analytics = (
            quantitative_analytics or QuantitativeAnalytics()
        )

        self.quantitative_evidence_service = (
            quantitative_evidence_service
            or QuantitativeEvidenceService()
        )

        self.higher_timeframe_context_service = (
            higher_timeframe_context_service
            or HigherTimeframeContextService()
        )

        self.fundamental_analysis_service = (
            fundamental_analysis_service
            or FundamentalAnalysisService()
        )

        self.evidence_builder = (
            evidence_builder or EvidenceBuilder()
        )

        self.opportunity_synthesis_service = (
            opportunity_synthesis_service
            or OpportunitySynthesisService()
        )

        self._last_higher_timeframe_context = None
        self._last_market_analysis = None

    @staticmethod
    def _supports_fundamental_analysis(
        symbol: str,
    ) -> bool:
        """
        Determine whether the symbol is suitable for
        currency-pair fundamental analysis.

        FundamentalAnalysisService is Forex-specific.
        Instruments such as XAUUSD must not be sent to it.
        """

        normalized_symbol = (
            symbol.strip()
            .upper()
            .replace("/", "")
        )

        if normalized_symbol == "XAUUSD":
            return False

        return (
            len(normalized_symbol) == 6
            and normalized_symbol.isalpha()
        )

    def build_evidence(
        self,
        candles: list[dict[str, Any]],
        daily_candles: list[dict[str, Any]],
        four_hour_candles: list[dict[str, Any]],
        forward_bars: int = 5,
        symbol: str | None = None,
        one_hour_candles: list[dict[str, Any]] | None = None,
    ) -> dict[str, EvidenceSource]:
        """
        Run Tradewisser's top-level analytical engines and return
        their results using the common Evidence Contract.

        When one_hour_candles are supplied, quantitative evidence
        is synthesized from both 4H and 1H quantitative analysis.

        If one_hour_candles are not supplied, the existing single-
        timeframe quantitative behavior is preserved for backward
        compatibility.

        Fundamental Analysis is included when a Forex symbol is
        supplied.
        """

        market_analysis = (
            self.market_analysis_service.analyze(candles)
        )

        # Preserve the raw market-analysis result for downstream
        # services that require the original analytical structure.
        self._last_market_analysis = market_analysis

        market_regime = (
            self.market_regime_service.classify(
                market_analysis
            )
        )

        if one_hour_candles is not None:
            four_hour_quantitative = (
                self.quantitative_analytics.analyze(
                    four_hour_candles,
                    forward_bars=forward_bars,
                )
            )

            one_hour_quantitative = (
                self.quantitative_analytics.analyze(
                    one_hour_candles,
                    forward_bars=forward_bars,
                )
            )

            quantitative_evidence = (
                self.quantitative_evidence_service.synthesize(
                    four_hour=four_hour_quantitative,
                    one_hour=one_hour_quantitative,
                )
            )

        else:
            quantitative_analysis = (
                self.quantitative_analytics.analyze(
                    candles,
                    forward_bars=forward_bars,
                )
            )

            quantitative_evidence = (
                self.evidence_builder.build_quantitative_analysis(
                    quantitative_analysis
                )
            )

        higher_timeframe_context = (
            self.higher_timeframe_context_service.analyze(
                daily_candles=daily_candles,
                four_hour_candles=four_hour_candles,
            )
        )

        self._last_higher_timeframe_context = (
            higher_timeframe_context
        )

        fundamental_analysis = None

        if (
            symbol
            and self._supports_fundamental_analysis(symbol)
        ):
            fundamental_analysis = (
                self.fundamental_analysis_service
                .analyze_from_provider(
                    symbol.replace("/", "")
                )
            )

        evidence: dict[str, EvidenceSource] = {
            "market_analysis": (
                self.evidence_builder.build_market_analysis(
                    market_analysis
                )
            ),
            "market_regime": (
                self.evidence_builder.build_market_regime(
                    market_regime.to_dict()
                )
            ),
            "quantitative_analytics": quantitative_evidence,
            "higher_timeframe_context": (
                self.evidence_builder.build_higher_timeframe_context(
                    higher_timeframe_context
                )
            ),
        }

        if fundamental_analysis is not None:
            evidence["fundamental_analysis"] = (
                self.evidence_builder.build_fundamental_analysis(
                    fundamental_analysis
                )
            )

        return evidence

    def get_last_higher_timeframe_context(
        self,
    ) -> dict[str, Any] | None:
        """
        Return the raw higher-timeframe context generated by the
        most recent build_evidence() call.
        """
        return self._last_higher_timeframe_context

    def get_last_market_analysis(
        self,
    ) -> Any | None:
        """
        Return the raw market-analysis result generated by the
        most recent build_evidence() call.
        """
        return self._last_market_analysis

    def assess_opportunity(
        self,
        evidence: dict[str, EvidenceSource],
    ) -> OpportunityAssessment:
        """
        Deterministically synthesize the market-level evidence
        sources into an OpportunityAssessment.

        This does not determine trade entry, position size, risk,
        or execution. It only determines whether the market-level
        evidence is strong enough to proceed to entry analysis.
        """

        return self.opportunity_synthesis_service.synthesize(
            evidence
        )

    @staticmethod
    def to_dict(
        evidence: dict[str, EvidenceSource],
    ) -> dict[str, Any]:
        """
        Serialize the complete evidence package into plain dictionaries.
        """

        return {
            source: evidence_source.to_dict()
            for source, evidence_source in evidence.items()
        }