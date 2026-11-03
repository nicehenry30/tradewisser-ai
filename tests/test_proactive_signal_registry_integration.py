from datetime import datetime

from app.models.analysis_request import AnalysisRequest
from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.market_watchlist_service import MarketWatchlistService
from app.services.proactive_scan_service import ProactiveScanService
from app.services.proactive_scanner_service import ProactiveScannerService
from app.services.signal_decision_service import SignalDecisionService


class FakeAnalysisService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def analyze(self, request):
        self.calls.append(request)
        return self.result


def make_request(symbol):
    return AnalysisRequest(
        symbol=symbol,
        account_balance=10000.0,
        risk_percent=1.0,
    )


def make_signal_analysis(
    status="AUTHORIZED",
    direction="BUY",
    opportunity="VALID",
):
    return {
        "status": status,
        "opportunity_assessment": {
            "direction": direction,
            "opportunity": opportunity,
        },
        "ai_interpretation": {
            "confidence": 0.85,
            "summary": "Bullish opportunity detected.",
        },
    }


def make_proactive_service(
    analysis_result,
    registry,
):
    watchlist_service = MarketWatchlistService()

    scanner_service = ProactiveScannerService(
        watchlist_service,
    )

    analysis_service = FakeAnalysisService(
        analysis_result,
    )

    signal_decision_service = SignalDecisionService()

    return (
        ProactiveScanService(
            scanner_service=scanner_service,
            analysis_service=analysis_service,
            request_factory=make_request,
            signal_decision_service=signal_decision_service,
            signal_registry=registry,
        ),
        analysis_service,
        scanner_service,
    )


def test_proactive_scan_registers_new_signal():
    registry = ActiveSignalRegistry()

    service, _, _ = make_proactive_service(
        make_signal_analysis(),
        registry,
    )

    now = datetime(2026, 11, 3, 10, 0)

    results = service.run_due_scans(now)

    signal_event = results[0]["signal_event"]

    assert signal_event is not None

    signal_id = results[0]["signal_id"]

    assert registry.get(signal_id) is signal_event


def test_proactive_scan_marks_new_signal_active():
    registry = ActiveSignalRegistry()

    service, _, _ = make_proactive_service(
        make_signal_analysis(),
        registry,
    )

    now = datetime(2026, 11, 3, 10, 0)

    results = service.run_due_scans(now)

    signal_id = results[0]["signal_id"]

    lifecycle = registry.get_lifecycle(signal_id)

    assert lifecycle is not None
    assert lifecycle.status == "ACTIVE"


def test_repeated_signal_does_not_create_duplicate_signal():
    registry = ActiveSignalRegistry()

    service, _, scanner = make_proactive_service(
        make_signal_analysis(),
        registry,
    )

    first_time = datetime(2026, 11, 3, 10, 0)

    first_results = service.run_due_scans(
        first_time
    )

    first_signal_id = first_results[0]["signal_id"]

    second_time = datetime(
        2026,
        11,
        3,
        10,
        5,
    )

    second_results = service.run_due_scans(
        second_time
    )

    assert second_results[0]["signal_id"] == first_signal_id


def test_different_direction_creates_new_signal():
    registry = ActiveSignalRegistry()

    service, analysis_service, _ = make_proactive_service(
        make_signal_analysis(
            direction="BUY",
        ),
        registry,
    )

    first_time = datetime(2026, 11, 3, 10, 0)

    first_results = service.run_due_scans(
        first_time
    )

    first_signal_id = first_results[0]["signal_id"]

    analysis_service.result = make_signal_analysis(
        direction="SELL",
    )

    # The scanner normally controls timing. For this test we
    # explicitly advance the scan interval.
    second_time = datetime(
        2026,
        11,
        3,
        10,
        5,
    )

    second_results = service.run_due_scans(
        second_time
    )

    second_signal_id = second_results[0]["signal_id"]

    assert second_signal_id != first_signal_id


def test_developing_signal_is_registered_but_not_active():
    registry = ActiveSignalRegistry()

    service, _, _ = make_proactive_service(
        make_signal_analysis(
            status="WAIT",
            opportunity="POTENTIAL",
        ),
        registry,
    )

    now = datetime(2026, 11, 3, 10, 0)

    results = service.run_due_scans(now)

    signal_event = results[0]["signal_event"]

    assert signal_event is not None
    assert signal_event.status == "DEVELOPING"

    signal_id = results[0]["signal_id"]

    lifecycle = registry.get_lifecycle(
        signal_id
    )

    assert lifecycle is not None
    assert lifecycle.status == "NEW"