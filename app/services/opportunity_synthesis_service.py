from __future__ import annotations

from typing import Any

from app.models.evidence import EvidenceSource
from app.models.opportunity_assessment import OpportunityAssessment
from app.services.evidence_quality_service import EvidenceQualityService
from app.models.evidence_quality import EvidenceQuality

class OpportunitySynthesisService:
    """
    Deterministically synthesizes Tradewisser's market-level
    evidence sources.

    Core market evidence:
        - market_analysis
        - market_regime
        - quantitative_analytics
        - higher_timeframe_context

    Fundamental Analysis is included as contextual evidence.
    It can support or conflict with the market evidence, but it
    cannot independently create a trade opportunity.

    This service does not:
        - calculate entries
        - calculate position size
        - calculate risk
        - execute trades
        - use an LLM

    Its responsibility is to determine whether the combined
    market evidence is strong enough to proceed to entry analysis.
    """

    CORE_SOURCE_ORDER = (
        "market_analysis",
        "market_regime",
        "quantitative_analytics",
        "higher_timeframe_context",
    )

    FUNDAMENTAL_SOURCE = "fundamental_analysis"

    SOURCE_ORDER = CORE_SOURCE_ORDER + (FUNDAMENTAL_SOURCE,)

    def __init__(
        self,
        evidence_quality_service: EvidenceQualityService | None = None,
    ):
        self.evidence_quality_service = (
            evidence_quality_service
            or EvidenceQualityService()
        )

    def _evaluate_source_quality(
        self,
        evidence: EvidenceSource,
    ):
        return self.evidence_quality_service.evaluate(evidence)

    def synthesize(
        self,
        evidence: dict[str, EvidenceSource],
    ) -> OpportunityAssessment:
        """
        Synthesize the available market-level evidence.

        Fundamental Analysis is treated as contextual evidence.
        It may support or conflict with the market direction, but
        it cannot independently create a valid opportunity.
        """

        normalized = self._normalize_evidence(evidence)
        source_quality = {
            source: self._evaluate_source_quality(evidence_source)
            for source, evidence_source in normalized.items()
        }

        core_evidence = {
            source: normalized[source]
            for source in self.CORE_SOURCE_ORDER
            if source in normalized
        }

        core_directions = {
            source: evidence_source.direction
            for source, evidence_source in core_evidence.items()
            if source_quality[source].quality
            in {"strong", "moderate", "unspecified"}
        }

        core_bullish_sources = [
            source
            for source, direction in core_directions.items()
            if direction == "bullish"
        ]

        core_bearish_sources = [
            source
            for source, direction in core_directions.items()
            if direction == "bearish"
        ]

        core_neutral_sources = [
            source
            for source, direction in core_directions.items()
            if direction == "neutral"
        ]

        bullish_count = len(core_bullish_sources)
        bearish_count = len(core_bearish_sources)

        direction = self._determine_direction(
            bullish_count=bullish_count,
            bearish_count=bearish_count,
        )

        agreement = self._determine_agreement(
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=len(core_neutral_sources),
            core_source_count=len(core_evidence),
        )

        opportunity = self._determine_opportunity(
            direction=direction,
            agreement=agreement,
            evidence=normalized,
            source_quality=source_quality,
        )

        supporting_sources = self._determine_supporting_sources(
            direction=direction,
            normalized=normalized,
        )

        conflicting_sources = self._determine_conflicts(
            direction=direction,
            normalized=normalized,
        )

        limitations = self._build_limitations(
            normalized=normalized,
            opportunity=opportunity,
            neutral_sources=core_neutral_sources,
            core_source_count=len(core_evidence),
        )

        proceed_to_entry = opportunity in {
            "VALID",
            "HIGH_QUALITY",
        }

        return OpportunityAssessment(
            direction=direction,
            opportunity=opportunity,
            agreement=agreement,
            proceed_to_entry=proceed_to_entry,
            supporting_sources=supporting_sources,
            conflicting_sources=conflicting_sources,
            limitations=limitations,
        )

    def _normalize_evidence(
        self,
        evidence: dict[str, EvidenceSource],
    ) -> dict[str, EvidenceSource]:
        """
        Keep only recognized evidence sources.

        Missing sources are not invented.
        """

        return {
            source: evidence[source]
            for source in self.SOURCE_ORDER
            if source in evidence
        }

    @staticmethod
    def _determine_direction(
        bullish_count: int,
        bearish_count: int,
    ) -> str:
        """
        Determine directional bias from core market evidence only.

        Fundamental Analysis does not vote directly on direction.
        """

        if bullish_count > bearish_count:
            return "LONG"

        if bearish_count > bullish_count:
            return "SHORT"

        return "NEUTRAL"

    @staticmethod
    def _determine_agreement(
        bullish_count: int,
        bearish_count: int,
        neutral_count: int,
        core_source_count: int,
    ) -> str:
        """
        Determine agreement using the core market evidence.

        The fundamental source is intentionally excluded from the
        directional vote.
        """

        directional_count = bullish_count + bearish_count

        if directional_count == 0:
            return "NONE"

        if bullish_count > 0 and bearish_count > 0:
            return "CONFLICTED"

        if (
            core_source_count == 4
            and neutral_count == 0
            and directional_count == 4
        ):
            return "HIGH"

        if directional_count >= 3:
            return "STRONG"

        if directional_count >= 2:
            return "MODERATE"

        return "WEAK"

    @staticmethod
    def _determine_opportunity(
        direction: str,
        agreement: str,
        evidence: dict[str, EvidenceSource],
        source_quality: dict[str, EvidenceQuality],
    ) -> str:
        """
        Determine opportunity quality from core market evidence.

        Fundamental Analysis cannot independently create an
        opportunity. When the core evidence is already strong,
        aligned fundamentals preserve HIGH_QUALITY, while conflicting
        fundamentals reduce HIGH_QUALITY to VALID.
        """

        # Conflicting directional evidence is a developing opportunity,
        # not automatically a dead market. It should be investigated
        # on the lower timeframes before any trade decision is made.
        if agreement == "CONFLICTED":
            return "POTENTIAL"

        if direction == "NEUTRAL":
            return "NO_OPPORTUNITY"

        if agreement == "HIGH":
            fundamental = evidence.get(
                OpportunitySynthesisService.FUNDAMENTAL_SOURCE
            )

            if fundamental is None:
                return "HIGH_QUALITY"

            if direction == "LONG":
                fundamental_direction = "bullish"
            elif direction == "SHORT":
                fundamental_direction = "bearish"
            else:
                fundamental_direction = "neutral"

            if fundamental.direction == "neutral":
                return "VALID"

            if fundamental.direction == fundamental_direction:
                return "HIGH_QUALITY"

            return "VALID"

        if agreement == "STRONG":
            return "VALID"

        if agreement == "MODERATE":
            return "POTENTIAL"

        return "NO_OPPORTUNITY"

    @staticmethod
    def _determine_supporting_sources(
        direction: str,
        normalized: dict[str, EvidenceSource],
    ) -> list[str]:
        """
        Return evidence sources aligned with the synthesized
        direction.

        Fundamental Analysis is included when it supports the
        direction.
        """

        if direction == "LONG":
            expected_direction = "bullish"
        elif direction == "SHORT":
            expected_direction = "bearish"
        else:
            return []

        return [
            source
            for source, evidence_source in normalized.items()
            if evidence_source.direction == expected_direction
        ]

    @staticmethod
    def _determine_conflicts(
        direction: str,
        normalized: dict[str, EvidenceSource],
    ) -> list[str]:
        """
        Return evidence sources that directly conflict with the
        synthesized direction.

        Fundamental Analysis is included only when there is an
        established market direction and the fundamental evidence
        disagrees with it.
        """

        if direction == "LONG":
            return [
                source
                for source, evidence_source in normalized.items()
                if evidence_source.direction == "bearish"
            ]

        if direction == "SHORT":
            return [
                source
                for source, evidence_source in normalized.items()
                if evidence_source.direction == "bullish"
            ]

        # With no synthesized market direction, there is no meaningful
        # supporting/conflicting relationship between evidence sources.
        return []

    @staticmethod
    def _build_limitations(
        normalized: dict[str, EvidenceSource],
        opportunity: str,
        neutral_sources: list[str],
        core_source_count: int,
    ) -> list[str]:
        limitations: list[str] = []

        if core_source_count < 4:
            limitations.append(
                "The synthesis package does not contain all four "
                "core market-level evidence sources."
            )

        if neutral_sources:
            limitations.append(
                "Some core market-level evidence sources are neutral."
            )

        fundamental = normalized.get(
            OpportunitySynthesisService.FUNDAMENTAL_SOURCE
        )

        if fundamental is None:
            limitations.append(
                "Fundamental Analysis is not available in this "
                "synthesis package."
            )
        elif fundamental.direction == "neutral":
            limitations.append(
                "Fundamental Analysis is neutral and does not "
                "provide directional macroeconomic support."
            )
        else:
            market_direction = (
                "bullish"
                if opportunity != "NO_OPPORTUNITY"
                and any(
                    source != OpportunitySynthesisService.FUNDAMENTAL_SOURCE
                    and evidence_source.direction == "bullish"
                    for source, evidence_source in normalized.items()
                )
                else "bearish"
                if opportunity != "NO_OPPORTUNITY"
                and any(
                    source != OpportunitySynthesisService.FUNDAMENTAL_SOURCE
                    and evidence_source.direction == "bearish"
                    for source, evidence_source in normalized.items()
                )
                else "neutral"
            )

            if (
                market_direction != "neutral"
                and fundamental.direction != market_direction
            ):
                limitations.append(
                    "Fundamental Analysis conflicts with the core "
                    "market evidence and should be interpreted "
                    "before entry confirmation."
                )

        if opportunity in {
            "NO_OPPORTUNITY",
            "POTENTIAL",
        }:
            limitations.append(
                "The evidence is not sufficient by itself to justify "
                "a trade entry."
            )

        limitations.append(
            "Entry confirmation must be evaluated separately on "
            "the 15M and 5M timeframes."
        )

        return limitations