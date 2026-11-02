from typing import Any

from app.services.fifteen_minute_setup_service import (
    FifteenMinuteSetupService,
)


class StubReversalFamilyDetector:
    def __init__(self, candidates=None):
        self.candidates = candidates or {
            "bullish": [],
            "bearish": [],
        }

    def detect(
        self,
        candles: list[dict[str, Any]],
        direction: str,
        timeframe: str,
    ):
        assert timeframe == "15m"
        return self.candidates.get(direction, [])


class StubStructureEngine:
    def __init__(self, structure: dict[str, Any]):
        self.structure = structure

    def analyze(
        self,
        candles: list[dict[str, Any]],
        timeframe: str,
    ) -> dict[str, Any]:
        assert timeframe == "15m"
        return self.structure


def make_structure(
    *,
    current_direction: str = "bullish",
    initial_direction: str = "bearish",
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "current_direction": current_direction,
        "initial_direction": initial_direction,
        "current_state": "test_state",
        "events": events or [],
    }


def make_event(
    event_type: str,
    direction: str,
    index: int,
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "direction": direction,
        "index": index,
    }


def make_service(
    structure: dict[str, Any],
    reversal_candidates=None,
) -> FifteenMinuteSetupService:
    return FifteenMinuteSetupService(
        structure_engine=StubStructureEngine(structure),
        reversal_family_detector=StubReversalFamilyDetector(
            reversal_candidates
        ),
    )


def bullish_context() -> dict[str, Any]:
    return {
        "preferred_direction": "BUY",
    }


def bearish_context() -> dict[str, Any]:
    return {
        "preferred_direction": "SELL",
    }


def test_reversal_choch_is_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bearish",
        events=[
            make_event("CHOCH", "bullish", 10),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] == "REVERSAL"
    assert result["setup_type"] == "REVERSAL_CHOCH"
    assert result["structure_pattern"] == ["CHOCH"]
    assert result["trigger"] == "CHOCH"
    assert result["direction"] == "bullish"
    assert result["qualified"] is True
    assert result["setup_stage"] == "READY_FOR_5M_CONFIRMATION"


def test_reversal_choch_bos_is_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bearish",
        events=[
            make_event("CHOCH", "bullish", 10),
            make_event("BOS", "bullish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] == "REVERSAL"
    assert result["setup_type"] == "REVERSAL_CHOCH_BOS"
    assert result["structure_pattern"] == ["CHOCH", "BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bullish"
    assert result["qualified"] is True
    assert result["setup_stage"] == "READY_FOR_5M_CONFIRMATION"


def test_continuation_bos_is_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bullish",
        events=[
            make_event("BOS", "bullish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] == "CONTINUATION"
    assert result["setup_type"] == "TREND_CONTINUATION_BOS"
    assert result["structure_pattern"] == ["BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bullish"
    assert result["qualified"] is True
    assert result["setup_stage"] == "READY_FOR_5M_CONFIRMATION"


def test_continuation_choch_bos_is_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bullish",
        events=[
            make_event("CHOCH", "bullish", 10),
            make_event("BOS", "bullish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] == "CONTINUATION"
    assert (
        result["setup_type"]
        == "TREND_CONTINUATION_CHOCH_BOS"
    )
    assert result["structure_pattern"] == ["CHOCH", "BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bullish"
    assert result["qualified"] is True
    assert result["setup_stage"] == "READY_FOR_5M_CONFIRMATION"


def test_generic_setup_contract_contains_required_fields():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bearish",
        events=[
            make_event("CHOCH", "bullish", 10),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert "setup_family" in result
    assert "setup_type" in result
    assert "structure_pattern" in result
    assert "trigger" in result
    assert "direction" in result
    assert "qualified" in result


def test_setup_is_ready_for_5m_confirmation_when_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bearish",
        events=[
            make_event("CHOCH", "bullish", 10),
            make_event("BOS", "bullish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["qualified"] is True
    assert result["setup_stage"] == "READY_FOR_5M_CONFIRMATION"
    assert result["confirmation_type"] == "5M_CONFIRMATION"
    assert result["confirmed"] is False


def test_no_structure_event_waits():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bullish",
        events=[],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] is None
    assert result["setup_type"] is None
    assert result["structure_pattern"] == []
    assert result["trigger"] is None
    assert result["qualified"] is False
    assert result["setup_stage"] == "WAIT"
    assert result["confirmation_type"] is None
    assert result["confirmed"] is False


def test_opposite_structure_is_not_qualified():
    structure = make_structure(
        current_direction="bearish",
        initial_direction="bearish",
        events=[
            make_event("BOS", "bearish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["direction"] == "neutral"
    assert result["setup_family"] is None
    assert result["setup_type"] is None
    assert result["qualified"] is False
    assert result["setup_stage"] == "WAIT"


def test_bearish_reversal_choch_is_qualified():
    structure = make_structure(
        current_direction="bearish",
        initial_direction="bullish",
        events=[
            make_event("CHOCH", "bearish", 10),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bearish_context(),
    )

    assert result["setup_family"] == "REVERSAL"
    assert result["setup_type"] == "REVERSAL_CHOCH"
    assert result["structure_pattern"] == ["CHOCH"]
    assert result["trigger"] == "CHOCH"
    assert result["direction"] == "bearish"
    assert result["qualified"] is True


def test_bearish_reversal_choch_bos_is_qualified():
    structure = make_structure(
        current_direction="bearish",
        initial_direction="bullish",
        events=[
            make_event("CHOCH", "bearish", 10),
            make_event("BOS", "bearish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bearish_context(),
    )

    assert result["setup_family"] == "REVERSAL"
    assert result["setup_type"] == "REVERSAL_CHOCH_BOS"
    assert result["structure_pattern"] == ["CHOCH", "BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bearish"
    assert result["qualified"] is True


def test_bearish_continuation_bos_is_qualified():
    structure = make_structure(
        current_direction="bearish",
        initial_direction="bearish",
        events=[
            make_event("BOS", "bearish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bearish_context(),
    )

    assert result["setup_family"] == "CONTINUATION"
    assert result["setup_type"] == "TREND_CONTINUATION_BOS"
    assert result["structure_pattern"] == ["BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bearish"
    assert result["qualified"] is True


def test_bearish_continuation_choch_bos_is_qualified():
    structure = make_structure(
        current_direction="bearish",
        initial_direction="bearish",
        events=[
            make_event("CHOCH", "bearish", 10),
            make_event("BOS", "bearish", 15),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bearish_context(),
    )

    assert result["setup_family"] == "CONTINUATION"
    assert (
        result["setup_type"]
        == "TREND_CONTINUATION_CHOCH_BOS"
    )
    assert result["structure_pattern"] == ["CHOCH", "BOS"]
    assert result["trigger"] == "BOS"
    assert result["direction"] == "bearish"
    assert result["qualified"] is True


def test_choch_without_bos_in_aligned_trend_is_not_qualified():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bullish",
        events=[
            make_event("CHOCH", "bullish", 10),
        ],
    )

    service = make_service(structure)

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert result["setup_family"] is None
    assert result["setup_type"] is None
    assert result["structure_pattern"] == []
    assert result["trigger"] is None
    assert result["direction"] == "bullish"
    assert result["qualified"] is False
    assert result["setup_stage"] == "WAIT"

def test_reversal_family_is_exposed_in_15m_result():
    structure = make_structure(
        current_direction="bullish",
        initial_direction="bearish",
        events=[],
    )

    reversal_candidates = {
        "bullish": [
            {
                "family": "repeated_level_reversal",
                "direction": "bullish",
                "timeframe": "15m",
                "state": "pullback_ready",
                "valid": True,
                "entry_candidate": True,
            }
        ],
        "bearish": [],
    }

    service = make_service(
        structure,
        reversal_candidates=reversal_candidates,
    )

    result = service.analyze(
        candles=[],
        higher_timeframe_context=bullish_context(),
    )

    assert "reversal_family" in result
    assert result["reversal_family"]["bullish"][0]["state"] == (
        "pullback_ready"
    )