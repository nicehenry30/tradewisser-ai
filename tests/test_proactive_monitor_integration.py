from datetime import datetime

from app.models.market_watchlist import MarketWatchlistItem
from app.services.market_watchlist_service import MarketWatchlistService
from app.services.proactive_monitor_service import ProactiveMonitorService
from app.services.proactive_scanner_service import ProactiveScannerService


class FakeAnalysisService:
    def __init__(self):
        self.requests = []

    def analyze(self, request):
        self.requests.append(request)

        return {
            "status": "WAIT",
            "opportunity_assessment": {
                "direction": "NEUTRAL",
                "opportunity": "NO_OPPORTUNITY",
            },
            "ai_interpretation": {
                "confidence": 0.0,
                "summary": "No actionable opportunity detected.",
            },
        }


class FakeRequest:
    def __init__(self, symbol):
        self.symbol = symbol


def test_monitor_runs_proactive_scan_pipeline():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                scan_interval_seconds=300,
                priority=1,
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    analysis_service = FakeAnalysisService()

    def request_factory(symbol):
        return FakeRequest(symbol)

    # Use the real ProactiveScanService and its dependencies.
    from app.services.proactive_scan_service import ProactiveScanService
    from app.services.signal_decision_service import SignalDecisionService

    scan_service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 10, 0, 0)

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        clock=lambda: now,
        sleep=lambda _: None,
    )

    results = monitor.run_once()

    assert len(results) == 1
    assert results[0]["symbol"] == "XAUUSD"
    assert results[0]["signal_event"] is None
    assert results[0]["signal_id"] is None
    assert results[0]["lifecycle"] is None

    assert len(analysis_service.requests) == 1
    assert analysis_service.requests[0].symbol == "XAUUSD"


def test_monitor_does_not_rescan_before_watchlist_interval():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                scan_interval_seconds=300,
                priority=1,
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    analysis_service = FakeAnalysisService()

    def request_factory(symbol):
        return FakeRequest(symbol)

    from app.services.proactive_scan_service import ProactiveScanService
    from app.services.signal_decision_service import SignalDecisionService

    scan_service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    current_time = datetime(2026, 11, 3, 10, 0, 0)

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        clock=lambda: current_time,
        sleep=lambda _: None,
    )

    first_result = monitor.run_once()

    assert len(first_result) == 1
    assert len(analysis_service.requests) == 1

    # Move only two minutes forward.
    current_time = datetime(2026, 11, 3, 10, 2, 0)

    second_result = monitor.run_once()

    assert second_result == []
    assert len(analysis_service.requests) == 1


def test_monitor_scans_again_after_watchlist_interval():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                scan_interval_seconds=300,
                priority=1,
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    analysis_service = FakeAnalysisService()

    def request_factory(symbol):
        return FakeRequest(symbol)

    from app.services.proactive_scan_service import ProactiveScanService
    from app.services.signal_decision_service import SignalDecisionService

    scan_service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    current_time = datetime(2026, 11, 3, 10, 0, 0)

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        clock=lambda: current_time,
        sleep=lambda _: None,
    )

    monitor.run_once()

    assert len(analysis_service.requests) == 1

    # Five minutes later the instrument becomes due again.
    current_time = datetime(2026, 11, 3, 10, 5, 0)

    result = monitor.run_once()

    assert len(result) == 1
    assert len(analysis_service.requests) == 2