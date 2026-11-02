from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from app.models.ai_interpretation import AIInterpretation
from app.models.evidence import EvidenceSource
from app.models.opportunity_assessment import OpportunityAssessment
from app.services.llm_service import LLMService


class _AIInterpretationSchema(BaseModel):
    """
    Internal structured-output schema used by the LLM.

    The public application model remains the dataclass
    AIInterpretation. This schema exists only to guarantee
    structured parsing from the Responses API.
    """

    summary: str
    reasoning: list[str]
    key_evidence: list[str]
    uncertainty: list[str]
    next_step: str
    limitations: list[str]


class AIInterpretationService:
    """
    Prepares a controlled interpretation package for Tradewisser AI.

    This service does not:
        - generate independent trading signals
        - calculate entries
        - calculate position size
        - calculate risk
        - execute trades

    The deterministic interpretation path remains available as
    a safe fallback and testable baseline.

    The LLM path only interprets deterministic evidence and the
    deterministic OpportunityAssessment.
    """

    def interpret(
        self,
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
    ) -> AIInterpretation:
        """
        Build a deterministic interpretation package.

        This path intentionally does not call an LLM.
        """
        reasoning = self._build_reasoning(evidence, assessment)
        key_evidence = self._build_key_evidence(evidence, assessment)
        uncertainty = self._build_uncertainty(evidence, assessment)
        next_step = self._determine_next_step(assessment)
        limitations = self._build_limitations(evidence, assessment)
        summary = self._build_summary(assessment)

        return AIInterpretation(
            summary=summary,
            reasoning=reasoning,
            key_evidence=key_evidence,
            uncertainty=uncertainty,
            next_step=next_step,
            limitations=limitations,
        )

    def interpret_with_llm(
        self,
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
        llm_service: LLMService | None = None,
    ) -> AIInterpretation:
        """
        Interpret deterministic market evidence with the LLM.

        The LLM is strictly downstream of the deterministic
        OpportunityAssessment.

        It may explain the evidence, but it may not:
            - override the opportunity assessment
            - invent market data
            - create an entry
            - calculate risk
            - calculate position size
            - execute a trade
        """

        llm = llm_service or LLMService()

        payload = {
            "evidence": {
                name: source.to_dict()
                for name, source in evidence.items()
            },
            "opportunity_assessment": assessment.to_dict(),
        }

        system_instruction = """
You are Tradewisser AI's market-evidence interpreter.

Your job is to interpret deterministic market evidence that has
already been calculated by Tradewisser's analytical engines.

IMPORTANT ARCHITECTURE RULES:

1. Treat the supplied evidence as authoritative input.
2. Do not invent current prices, candles, indicators, market data,
   historical observations, or facts that are not present.
3. Do not independently generate a BUY or SELL signal.
4. Do not calculate an entry price.
5. Do not calculate stop loss or take profit.
6. Do not calculate position size.
7. Do not calculate or approve risk.
8. Do not execute or recommend execution of a trade.
9. Do not override the supplied OpportunityAssessment.
10. If the OpportunityAssessment says NO_OPPORTUNITY, the next_step
    must be WAIT.
11. If the OpportunityAssessment says POTENTIAL, the next_step must
    be WAIT.
12. Only VALID or HIGH_QUALITY opportunities may proceed to
    entry analysis.
13. The next step must therefore remain:
       PROCEED_TO_ENTRY_ANALYSIS
    only when the deterministic assessment itself permits it.
14. Clearly distinguish evidence from uncertainty.
15. Historical evidence describes what happened under similar
    conditions; it does not guarantee future behavior.
16. Higher-Timeframe Context describes context and reference levels;
    it does not independently determine entry.
17. Market Analysis, Market Regime, Quantitative Analytics,
Higher-Timeframe Context and Fundamental Analysis are evidence
sources, not competing trading signals.

18. Fundamental Analysis provides macroeconomic and monetary-policy
context. It must not independently create, promote, or reject an
opportunity.

19. If Fundamental Analysis contains unavailable or incomplete
macro data, clearly state that limitation rather than inferring or
inventing economic conditions.

20. High-impact fundamental events may increase uncertainty or event
risk, but they do not independently determine trade direction.

Return a concise, professional interpretation for a trading system.
"""

        user_input = (
            "Interpret the following deterministic Tradewisser market "
            "evidence and opportunity assessment.\n\n"
            + json.dumps(payload, indent=2, default=str)
        )

        response = llm.ask_structured(
            input=[
                {
                    "role": "system",
                    "content": system_instruction,
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
            text_format=_AIInterpretationSchema,
        )

        parsed = getattr(response, "output_parsed", None)

        if parsed is None:
            raise ValueError(
                "LLM structured response did not contain output_parsed."
            )

        # The deterministic assessment remains authoritative.
        # Never allow the LLM to promote or demote the opportunity.
        enforced_next_step = self._determine_next_step(assessment)

        return AIInterpretation(
            summary=parsed.summary,
            reasoning=parsed.reasoning,
            key_evidence=parsed.key_evidence,
            uncertainty=parsed.uncertainty,
            next_step=enforced_next_step,
            limitations=list(
                dict.fromkeys(
                    [
                        *parsed.limitations,
                        *assessment.limitations,
                    ]
                )
            ),
        )

    @staticmethod
    def _build_summary(
        assessment: OpportunityAssessment,
    ) -> str:
        if assessment.opportunity == "HIGH_QUALITY":
            return (
                f"{assessment.direction} market opportunity with strong "
                "agreement across the available market-level evidence."
            )

        if assessment.opportunity == "VALID":
            return (
                f"{assessment.direction} market opportunity with "
                "meaningful agreement across the market-level evidence."
            )

        if assessment.opportunity == "POTENTIAL":
            return (
                f"{assessment.direction} opportunity is possible, "
                "but the available evidence is not sufficiently strong."
            )

        return (
            "The available market-level evidence does not establish "
            "a sufficient trading opportunity."
        )

    @staticmethod
    def _build_reasoning(
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
    ) -> list[str]:
        reasoning: list[str] = []

        if assessment.direction != "NEUTRAL":
            reasoning.append(
                f"The combined evidence currently favors "
                f"{assessment.direction}."
            )

        if assessment.agreement == "HIGH":
            reasoning.append(
                "All available market-level evidence sources are "
                "directionally aligned."
            )
        elif assessment.agreement == "STRONG":
            reasoning.append(
                "Most market-level evidence sources are "
                "directionally aligned."
            )
        elif assessment.agreement == "MODERATE":
            reasoning.append(
                "Only moderate directional agreement exists "
                "across the evidence."
            )
        elif assessment.agreement == "WEAK":
            reasoning.append(
                "Only one directional evidence source supports "
                "the current direction."
            )
        elif assessment.agreement == "CONFLICTED":
            reasoning.append(
                "Bullish and bearish evidence sources are conflicting."
            )
        else:
            reasoning.append(
                "The available evidence does not establish "
                "directional agreement."
            )

        if assessment.supporting_sources:
            reasoning.append(
                "Supporting evidence comes from: "
                + ", ".join(assessment.supporting_sources)
                + "."
            )

        if assessment.conflicting_sources:
            reasoning.append(
                "Conflicting evidence comes from: "
                + ", ".join(assessment.conflicting_sources)
                + "."
            )

        return reasoning

    @staticmethod
    def _build_key_evidence(
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
    ) -> list[str]:
        key_evidence: list[str] = []

        for source_name in assessment.supporting_sources:
            source = evidence.get(source_name)

            if source is None:
                continue

            key_evidence.append(
                f"{source_name}: direction={source.direction}"
            )

        if not key_evidence:
            for source_name, source in evidence.items():
                key_evidence.append(
                    f"{source_name}: direction={source.direction}"
                )

        return key_evidence

    @staticmethod
    def _build_uncertainty(
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
    ) -> list[str]:
        uncertainty: list[str] = []

        if assessment.conflicting_sources:
            uncertainty.append(
                "Some evidence sources disagree with the "
                "prevailing direction."
            )

        if assessment.opportunity in {
            "NO_OPPORTUNITY",
            "POTENTIAL",
        }:
            uncertainty.append(
                "The market-level evidence is not sufficient by "
                "itself to justify a trade entry."
            )

        for source in evidence.values():
            if source.limitations:
                uncertainty.extend(source.limitations)

        if not uncertainty:
            uncertainty.append(
                "Historical and structural evidence cannot "
                "guarantee future price behavior."
            )

        return list(dict.fromkeys(uncertainty))

    @staticmethod
    def _determine_next_step(
        assessment: OpportunityAssessment,
    ) -> str:
        if (
            assessment.opportunity
            in {"VALID", "HIGH_QUALITY"}
            and assessment.proceed_to_entry
        ):
            return "PROCEED_TO_ENTRY_ANALYSIS"

        return "WAIT"

    @staticmethod
    def _build_limitations(
        evidence: dict[str, EvidenceSource],
        assessment: OpportunityAssessment,
    ) -> list[str]:
        limitations = list(assessment.limitations)

        for source in evidence.values():
            limitations.extend(source.limitations)

        return list(dict.fromkeys(limitations))