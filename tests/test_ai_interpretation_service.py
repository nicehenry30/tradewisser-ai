from app.models.ai_interpretation import AIInterpretation
from app.models.evidence import EvidenceSource
from app.models.opportunity_assessment import OpportunityAssessment
from app.services.ai_interpretation_service import (
    AIInterpretationService,
)

def make_evidence(
    market_analysis="bullish",
    market_regime="bullish",
    quantitative="bullish",
    higher_timeframe="bullish",
    fundamental=None,
):
    evidence = {
        "market_analysis": EvidenceSource(
            source="market_analysis",
            direction=market_analysis,
        ),
        "market_regime": EvidenceSource(
            source="market_regime",
            direction=market_regime,
        ),
        "quantitative_analytics": EvidenceSource(
            source="quantitative_analytics",
            direction=quantitative,
        ),
        "higher_timeframe_context": EvidenceSource(
            source="higher_timeframe_context",
            direction=higher_timeframe,
        ),
    }

    if fundamental is not None:
        evidence["fundamental_analysis"] = fundamental

    return evidence


def make_assessment(
    direction="LONG",
    opportunity="HIGH_QUALITY",
    agreement="HIGH",
    proceed_to_entry=True,
    supporting_sources=None,
    conflicting_sources=None,
    limitations=None,
):
    return OpportunityAssessment(
        direction=direction,
        opportunity=opportunity,
        agreement=agreement,
        proceed_to_entry=proceed_to_entry,
        supporting_sources=(
            supporting_sources
            if supporting_sources is not None
            else [
                "market_analysis",
                "market_regime",
                "quantitative_analytics",
                "higher_timeframe_context",
            ]
        ),
        conflicting_sources=(
            conflicting_sources
            if conflicting_sources is not None
            else []
        ),
        limitations=limitations if limitations is not None else [],
    )


def test_high_quality_opportunity_produces_entry_analysis_next_step():
    service = AIInterpretationService()

    interpretation = service.interpret(
        evidence=make_evidence(),
        assessment=make_assessment(),
    )

    assert "LONG" in interpretation.summary
    assert interpretation.next_step == "PROCEED_TO_ENTRY_ANALYSIS"
    assert interpretation.reasoning
    assert interpretation.key_evidence
    assert interpretation.uncertainty
    assert interpretation.limitations == []


def test_no_opportunity_produces_wait_next_step():
    service = AIInterpretationService()

    interpretation = service.interpret(
        evidence=make_evidence(
            market_analysis="neutral",
            market_regime="neutral",
            quantitative="neutral",
            higher_timeframe="neutral",
        ),
        assessment=make_assessment(
            direction="NEUTRAL",
            opportunity="NO_OPPORTUNITY",
            agreement="NONE",
            proceed_to_entry=False,
            supporting_sources=[],
        ),
    )

    assert "sufficient trading opportunity" in interpretation.summary
    assert interpretation.next_step == "WAIT"
    assert interpretation.uncertainty


def test_conflicting_evidence_is_explicitly_reported():
    service = AIInterpretationService()

    evidence = make_evidence(
        market_analysis="bullish",
        market_regime="bearish",
        quantitative="bullish",
        higher_timeframe="bearish",
    )

    assessment = make_assessment(
        direction="NEUTRAL",
        opportunity="NO_OPPORTUNITY",
        agreement="CONFLICTED",
        proceed_to_entry=False,
        supporting_sources=[],
        conflicting_sources=[
            "market_analysis",
            "quantitative_analytics",
        ],
    )

    interpretation = service.interpret(
        evidence=evidence,
        assessment=assessment,
    )

    assert interpretation.next_step == "WAIT"
    assert any(
        "disagree" in item.lower()
        for item in interpretation.uncertainty
    )


def test_source_limitations_are_propagated():
    service = AIInterpretationService()

    evidence = make_evidence()

    evidence["quantitative_analytics"] = EvidenceSource(
        source="quantitative_analytics",
        direction="bullish",
        limitations=[
            "Historical outcomes are not guarantees."
        ],
    )

    interpretation = service.interpret(
        evidence=evidence,
        assessment=make_assessment(),
    )

    assert (
        "Historical outcomes are not guarantees."
        in interpretation.uncertainty
    )
    assert (
        "Historical outcomes are not guarantees."
        in interpretation.limitations
    )


def test_interpretation_serializes_correctly():
    service = AIInterpretationService()

    interpretation = service.interpret(
        evidence=make_evidence(),
        assessment=make_assessment(),
    )

    serialized = interpretation.to_dict()

    assert serialized["summary"]
    assert isinstance(serialized["reasoning"], list)
    assert isinstance(serialized["key_evidence"], list)
    assert isinstance(serialized["uncertainty"], list)
    assert serialized["next_step"] == "PROCEED_TO_ENTRY_ANALYSIS"
    assert isinstance(serialized["limitations"], list)

class StubStructuredResponse:
    def __init__(self, output_parsed):
        self.output_parsed = output_parsed


class StubLLMService:
    def __init__(self, interpretation):
        self.interpretation = interpretation
        self.calls = []

    def ask_structured(self, input, text_format):
        self.calls.append(
            {
                "input": input,
                "text_format": text_format,
            }
        )

        return StubStructuredResponse(self.interpretation)


def test_llm_interpretation_uses_structured_output():
    service = AIInterpretationService()

    evidence = make_evidence(
        market_analysis="bullish",
        market_regime="bullish",
        quantitative="bullish",
        higher_timeframe="bullish",
    )

    assessment = OpportunityAssessment(
        direction="LONG",
        opportunity="HIGH_QUALITY",
        agreement="HIGH",
        proceed_to_entry=True,
        supporting_sources=[
            "market_analysis",
            "market_regime",
            "quantitative_analytics",
            "higher_timeframe_context",
        ],
    )

    llm = StubLLMService(
        AIInterpretation(
            summary="Strong bullish evidence.",
            reasoning=["The evidence is aligned."],
            key_evidence=["Market structure is bullish."],
            uncertainty=["Future price behavior remains uncertain."],
            next_step="PROCEED_TO_ENTRY_ANALYSIS",
            limitations=[],
        )
    )

    result = service.interpret_with_llm(
        evidence,
        assessment,
        llm_service=llm,
    )

    assert result.summary == "Strong bullish evidence."
    assert result.next_step == "PROCEED_TO_ENTRY_ANALYSIS"
    assert len(llm.calls) == 1


def test_llm_cannot_override_wait_decision():
    service = AIInterpretationService()

    evidence = make_evidence(
        market_analysis="bullish",
        market_regime="neutral",
        quantitative="neutral",
        higher_timeframe="neutral",
    )

    assessment = OpportunityAssessment(
        direction="LONG",
        opportunity="POTENTIAL",
        agreement="WEAK",
        proceed_to_entry=False,
        supporting_sources=["market_analysis"],
    )

    # Deliberately make the fake LLM attempt to override
    # the deterministic assessment.
    llm = StubLLMService(
        AIInterpretation(
            summary="The market looks ready.",
            reasoning=["Bullish conditions appear favorable."],
            key_evidence=["Bullish market analysis."],
            uncertainty=[],
            next_step="PROCEED_TO_ENTRY_ANALYSIS",
            limitations=[],
        )
    )

    result = service.interpret_with_llm(
        evidence,
        assessment,
        llm_service=llm,
    )

    assert result.next_step == "WAIT"


def test_llm_cannot_promote_no_opportunity():
    service = AIInterpretationService()

    evidence = make_evidence(
        market_analysis="neutral",
        market_regime="neutral",
        quantitative="neutral",
        higher_timeframe="neutral",
    )

    assessment = OpportunityAssessment(
        direction="NEUTRAL",
        opportunity="NO_OPPORTUNITY",
        agreement="NONE",
        proceed_to_entry=False,
    )

    llm = StubLLMService(
        AIInterpretation(
            summary="Possible opportunity detected.",
            reasoning=["The market may be preparing to move."],
            key_evidence=[],
            uncertainty=[],
            next_step="PROCEED_TO_ENTRY_ANALYSIS",
            limitations=[],
        )
    )

    result = service.interpret_with_llm(
        evidence,
        assessment,
        llm_service=llm,
    )

    assert result.next_step == "WAIT"

def test_fundamental_evidence_is_included_in_interpretation():
    service = AIInterpretationService()

    fundamental = EvidenceSource(
        source="fundamental_analysis",
        direction="neutral",
        confidence=0.0,
        observations=[],
        limitations=[
            "macro_indicator_data_unavailable_from_current_provider",
            "high_impact_event_risk",
        ],
    )

    interpretation = service.interpret(
        evidence=make_evidence(
            fundamental=fundamental,
        ),
        assessment=make_assessment(
            limitations=[
                "Fundamental analysis is currently limited by available macro data."
            ],
        ),
    )

    assert any(
        "macro_indicator_data_unavailable_from_current_provider" in item
        for item in interpretation.uncertainty
    )

    assert any(
        "Fundamental analysis is currently limited"
        in item
        for item in interpretation.limitations
    )


def test_fundamental_analysis_does_not_override_deterministic_assessment():
    service = AIInterpretationService()

    fundamental = EvidenceSource(
        source="fundamental_analysis",
        direction="bullish",
        confidence=1.0,
    )

    interpretation = service.interpret(
        evidence=make_evidence(
            market_analysis="neutral",
            market_regime="neutral",
            quantitative="neutral",
            higher_timeframe="neutral",
            fundamental=fundamental,
        ),
        assessment=make_assessment(
            direction="NEUTRAL",
            opportunity="NO_OPPORTUNITY",
            agreement="NONE",
            proceed_to_entry=False,
            supporting_sources=[],
        ),
    )

    assert interpretation.next_step == "WAIT"


def test_fundamental_limitations_are_propagated():
    service = AIInterpretationService()

    fundamental = EvidenceSource(
        source="fundamental_analysis",
        direction="neutral",
        confidence=0.0,
        limitations=[
            "macro_indicator_data_unavailable_from_current_provider",
            "high_impact_event_risk",
        ],
    )

    interpretation = service.interpret(
        evidence=make_evidence(
            fundamental=fundamental,
        ),
        assessment=make_assessment(),
    )

    assert (
        "macro_indicator_data_unavailable_from_current_provider"
        in interpretation.uncertainty
    )

    assert "high_impact_event_risk" in interpretation.uncertainty

    assert (
        "macro_indicator_data_unavailable_from_current_provider"
        in interpretation.limitations
    )