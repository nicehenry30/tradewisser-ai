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
        # POTENTIAL means the market deserves lower-timeframe
        # investigation, but it is NOT approved for trade entry.
        proceed_to_entry_analysis = assessment.opportunity in {
            "POTENTIAL",
            "VALID",
            "HIGH_QUALITY",
        }

        if assessment.opportunity == "POTENTIAL":
            ai_next_step = "INVESTIGATE_LOWER_TIMEFRAME"
        elif (
            assessment.opportunity in {"VALID", "HIGH_QUALITY"}
            and assessment.proceed_to_entry
        ):
            ai_next_step = "PROCEED_TO_ENTRY_ANALYSIS"
        else:
            ai_next_step = "WAIT"

        return EntryAnalysisContext(
            direction=assessment.direction,
            opportunity=assessment.opportunity,
            proceed_to_entry_analysis=proceed_to_entry_analysis,
            ai_next_step=ai_next_step,
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