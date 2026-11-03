from datetime import datetime, timezone

from app.models.signal_event import SignalEvent
from app.services.signal_decision_service import SignalDecisionService


def test_authorized_analysis_creates_signal_event():
    service = SignalDecisionService()

    result = {
        "status": "AUTHORIZED",
        "opportunity_assessment": {
            "direction": "BUY",
        },
        "ai_interpretation": {
            "confidence": 0.9,
            "summary": "Strong bullish confirmation.",
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert isinstance(event, SignalEvent)
    assert event.symbol == "XAUUSD"
    assert event.direction == "BUY"
    assert event.status == "SIGNAL"
    assert event.confidence == 0.9


def test_waiting_analysis_does_not_create_signal():
    service = SignalDecisionService()

    result = {
        "status": "WAIT",
        "opportunity_assessment": {
            "direction": "BUY",
        },
        "ai_interpretation": {
            "confidence": 0.5,
            "summary": "Waiting for confirmation.",
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert event is None


def test_potential_analysis_creates_developing_event():
    service = SignalDecisionService()

    result = {
        "status": "WAIT",
        "opportunity_assessment": {
            "direction": "BUY",
            "opportunity": "POTENTIAL",
        },
        "ai_interpretation": {
            "confidence": 0.65,
            "summary": "Potential bullish setup.",
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert isinstance(event, SignalEvent)
    assert event.status == "DEVELOPING"
    assert event.direction == "BUY"
    assert event.confidence == 0.65


def test_rejected_analysis_does_not_create_signal():
    service = SignalDecisionService()

    result = {
        "status": "RISK_REJECTED",
        "opportunity_assessment": {
            "direction": "BUY",
        },
        "ai_interpretation": {
            "confidence": 0.95,
            "summary": "Strong setup.",
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert event is None

def test_confirmed_analysis_creates_confirmed_event():
    service = SignalDecisionService()

    result = {
        "status": "WAIT",
        "opportunity_assessment": {
            "direction": "BUY",
            "opportunity": "POTENTIAL",
        },
        "ai_interpretation": {
            "confidence": 0.78,
            "summary": "Lower timeframe confirmation supports the developing setup.",
        },
        "five_minute_confirmation": {
            "confirmed": True,
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert isinstance(event, SignalEvent)
    assert event.status == "CONFIRMED"
    assert event.direction == "BUY"
    assert event.confidence == 0.78
    

def test_potential_analysis_without_confirmation_remains_developing():
    service = SignalDecisionService()

    result = {
        "status": "WAIT",
        "opportunity_assessment": {
            "direction": "BUY",
            "opportunity": "POTENTIAL",
        },
        "ai_interpretation": {
            "confidence": 0.65,
            "summary": "Potential bullish setup.",
        },
        "five_minute_confirmation": {
            "confirmed": False,
        },
    }

    event = service.evaluate(
        symbol="XAUUSD",
        analysis_result=result,
        detected_at=datetime.now(timezone.utc),
    )

    assert isinstance(event, SignalEvent)
    assert event.status == "DEVELOPING"
    assert event.direction == "BUY"
