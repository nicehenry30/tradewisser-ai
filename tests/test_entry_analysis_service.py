from app.models.ai_interpretation import AIInterpretation
from app.models.entry_analysis_context import EntryAnalysisContext
from app.services.entry_analysis_service import EntryAnalysisService


class StubFifteenMinuteSetupService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def analyze(self, candles, higher_timeframe_context):
        self.calls.append(
            {
                "candles": candles,
                "higher_timeframe_context": higher_timeframe_context,
            }
        )
        return self.result


def make_context(
    proceed_to_entry_analysis=True,
):
    return EntryAnalysisContext(
        direction="LONG",
        opportunity="HIGH_QUALITY",
        proceed_to_entry_analysis=proceed_to_entry_analysis,
        ai_next_step=(
            "PROCEED_TO_ENTRY_ANALYSIS"
            if proceed_to_entry_analysis
            else "WAIT"
        ),
        supporting_sources=[
            "market_analysis",
            "market_regime",
            "quantitative_analytics",
            "higher_timeframe_context",
        ],
    )


def test_blocked_context_does_not_call_15m_service():
    stub = StubFifteenMinuteSetupService(
        {
            "qualified": True,
        }
    )

    service = EntryAnalysisService(
        fifteen_minute_setup_service=stub,
    )

    result = service.analyze(
        context=make_context(
            proceed_to_entry_analysis=False,
        ),
        candles=[{"close": 100}],
        higher_timeframe_context={
            "preferred_direction": "BUY",
        },
    )

    assert result["status"] == "WAIT"
    assert result["proceed_to_confirmation"] is False
    assert result["setup"] is None
    assert stub.calls == []


def test_authorized_context_calls_15m_service():
    stub = StubFifteenMinuteSetupService(
        {
            "qualified": False,
            "setup_type": None,
        }
    )

    service = EntryAnalysisService(
        fifteen_minute_setup_service=stub,
    )

    candles = [
        {"close": 100},
        {"close": 101},
    ]

    htf_context = {
        "preferred_direction": "BUY",
    }

    result = service.analyze(
        context=make_context(),
        candles=candles,
        higher_timeframe_context=htf_context,
    )

    assert len(stub.calls) == 1
    assert stub.calls[0]["candles"] == candles
    assert stub.calls[0]["higher_timeframe_context"] == htf_context


def test_qualified_15m_setup_proceeds_to_confirmation():
    stub = StubFifteenMinuteSetupService(
        {
            "timeframe": "15m",
            "setup_type": "CHOCH",
            "setup_priority": "primary",
            "qualified": True,
        }
    )

    service = EntryAnalysisService(
        fifteen_minute_setup_service=stub,
    )

    result = service.analyze(
        context=make_context(),
        candles=[{"close": 100}],
        higher_timeframe_context={
            "preferred_direction": "BUY",
        },
    )

    assert result["status"] == "QUALIFIED"
    assert result["proceed_to_confirmation"] is True
    assert result["setup"]["qualified"] is True
    assert result["setup"]["setup_type"] == "CHOCH"


def test_unqualified_15m_setup_stops_progression():
    stub = StubFifteenMinuteSetupService(
        {
            "timeframe": "15m",
            "setup_type": None,
            "qualified": False,
        }
    )

    service = EntryAnalysisService(
        fifteen_minute_setup_service=stub,
    )

    result = service.analyze(
        context=make_context(),
        candles=[{"close": 100}],
        higher_timeframe_context={
            "preferred_direction": "BUY",
        },
    )

    assert result["status"] == "WAIT"
    assert result["proceed_to_confirmation"] is False
    assert result["setup"]["qualified"] is False


def test_15m_qualification_does_not_mean_entry():
    stub = StubFifteenMinuteSetupService(
        {
            "timeframe": "15m",
            "setup_type": "BOS",
            "setup_priority": "secondary",
            "qualified": True,
        }
    )

    service = EntryAnalysisService(
        fifteen_minute_setup_service=stub,
    )

    result = service.analyze(
        context=make_context(),
        candles=[{"close": 100}],
        higher_timeframe_context={
            "preferred_direction": "BUY",
        },
    )

    assert result["status"] == "QUALIFIED"
    assert result["proceed_to_confirmation"] is True

    # The orchestration layer does not produce an entry instruction.
    assert "entry_price" not in result
    assert "stop_loss" not in result
    assert "take_profit" not in result
    assert "position_size" not in result
    assert "execute_trade" not in result