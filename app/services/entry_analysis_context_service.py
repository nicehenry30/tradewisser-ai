from __future__ import annotations

from app.models.ai_interpretation import AIInterpretation
from app.models.entry_analysis_context import EntryAnalysisContext
from app.models.opportunity_assessment import OpportunityAssessment


class EntryAnalysisContextService:
    """
    Creates the controlled boundary between AI interpretation
    and the entry-analysis layer.

    The deterministic OpportunityAssessment remains authoritative.
    """

    def build(
        self,
        assessment: OpportunityAssessment,
        interpretation: AIInterpretation,
    ) -> EntryAnalysisContext:
        proceed = (
            assessment.opportunity in {"VALID", "HIGH_QUALITY"}
            and assessment.proceed_to_entry
        )

        return EntryAnalysisContext(
            direction=assessment.direction,
            opportunity=assessment.opportunity,
            proceed_to_entry_analysis=proceed,
            ai_next_step=(
                "PROCEED_TO_ENTRY_ANALYSIS"
                if proceed
                else "WAIT"
            ),
            supporting_sources=list(
                assessment.supporting_sources
            ),
            conflicting_sources=list(
                assessment.conflicting_sources
            ),
            key_evidence=list(
                interpretation.key_evidence
            ),
            uncertainty=list(
                interpretation.uncertainty
            ),
            limitations=list(
                dict.fromkeys(
                    [
                        *assessment.limitations,
                        *interpretation.limitations,
                    ]
                )
            ),
        )