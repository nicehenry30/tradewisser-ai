from opentelemetry import context

from app.models.ai_interpretation import AIInterpretation
from app.models.opportunity_assessment import OpportunityAssessment
from app.services.entry_analysis_context_service import (
    EntryAnalysisContextService,
)


def make_assessment(
    opportunity="HIGH_QUALITY",
    proceed_to_entry=True,
):
    return OpportunityAssessment(
        direction="LONG",
        opportunity=opportunity,
        agreement="HIGH",
        proceed_to_entry=proceed_to_entry,
        supporting_sources=[
            "market_analysis",
            "market_regime",
            "quantitative_analytics",
            "higher_timeframe_context",
        ],
    )


def make_interpretation(
    next_step="PROCEED_TO_ENTRY_ANALYSIS",
):
    return AIInterpretation(
        summary="Bullish market opportunity.",
        reasoning=["The available evidence is aligned."],
        key_evidence=["Market structure is bullish."],
        uncertainty=["Future price behavior is uncertain."],
        next_step=next_step,
        limitations=[],
    )


def test_valid_opportunity_allows_entry_analysis():
    service = EntryAnalysisContextService()

    context = service.build(
        assessment=make_assessment(
            opportunity="VALID",
            proceed_to_entry=True,
        ),
        interpretation=make_interpretation(),
    )

    assert context.direction == "LONG"
    assert context.opportunity == "VALID"
    assert context.proceed_to_entry_analysis is True
    assert context.ai_next_step == "PROCEED_TO_ENTRY_ANALYSIS"


def test_high_quality_opportunity_allows_entry_analysis():
    service = EntryAnalysisContextService()

    context = service.build(
        assessment=make_assessment(),
        interpretation=make_interpretation(),
    )

    assert context.proceed_to_entry_analysis is True
    assert context.ai_next_step == "PROCEED_TO_ENTRY_ANALYSIS"


def test_potential_opportunity_allows_lower_timeframe_investigation():
    service = EntryAnalysisContextService()

    context = service.build(
        assessment=make_assessment(
            opportunity="POTENTIAL",
            proceed_to_entry=False,
        ),
        interpretation=make_interpretation(
            next_step="PROCEED_TO_ENTRY_ANALYSIS",
        ),
    )

    assert context.proceed_to_entry_analysis is True
    assert context.ai_next_step == "INVESTIGATE_LOWER_TIMEFRAME"


def test_no_opportunity_blocks_entry_analysis():
    service = EntryAnalysisContextService()

    context = service.build(
        assessment=OpportunityAssessment(
            direction="NEUTRAL",
            opportunity="NO_OPPORTUNITY",
            agreement="NONE",
            proceed_to_entry=False,
        ),
        interpretation=make_interpretation(
            next_step="PROCEED_TO_ENTRY_ANALYSIS",
        ),
    )

    assert context.proceed_to_entry_analysis is False
    assert context.ai_next_step == "WAIT"


def test_context_preserves_evidence_and_uncertainty():
    service = EntryAnalysisContextService()

    interpretation = AIInterpretation(
        summary="Bullish opportunity.",
        reasoning=["Evidence is aligned."],
        key_evidence=[
            "market_analysis: bullish",
            "quantitative_analytics: bullish",
        ],
        uncertainty=[
            "Historical outcomes are not guarantees."
        ],
        next_step="PROCEED_TO_ENTRY_ANALYSIS",
        limitations=[
            "Entry confirmation is still required."
        ],
    )

    context = service.build(
        assessment=make_assessment(),
        interpretation=interpretation,
    )

    assert context.key_evidence == [
        "market_analysis: bullish",
        "quantitative_analytics: bullish",
    ]

    assert (
        "Historical outcomes are not guarantees."
        in context.uncertainty
    )

    assert (
        "Entry confirmation is still required."
        in context.limitations
    )


def test_context_serializes_correctly():
    service = EntryAnalysisContextService()

    context = service.build(
        assessment=make_assessment(),
        interpretation=make_interpretation(),
    )

    serialized = context.to_dict()

    assert serialized["direction"] == "LONG"
    assert serialized["opportunity"] == "HIGH_QUALITY"
    assert serialized["proceed_to_entry_analysis"] is True
    assert isinstance(serialized["key_evidence"], list)
    assert isinstance(serialized["uncertainty"], list)
    assert isinstance(serialized["limitations"], list)