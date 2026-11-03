from datetime import datetime, timezone

from app.models.analysis_request import AnalysisRequest
from app.models.market_watchlist import MarketWatchlistItem
from app.services.market_watchlist_service import MarketWatchlistService
from app.services.proactive_scanner_service import ProactiveScannerService
from app.services.proactive_scan_service import ProactiveScanService
from app.services.signal_decision_service import SignalDecisionService


def build_request(symbol: str) -> AnalysisRequest:
    return AnalysisRequest(
        symbol=symbol,
        account_balance=10000.0,
        risk_percent=1.0,
    )


def test_proactive_scan_can_create_signal_event():
    watchlist = MarketWatchlistService(
        [
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    class FakeAnalysisService:
        def analyze(self, request):
            return {
                "status": "AUTHORIZED",
                "opportunity_assessment": {
                    "direction": "BUY",
                },
                "ai_interpretation": {
                    "confidence": 0.9,
                    "summary": "Strong bullish confirmation.",
                },
            }

    service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=FakeAnalysisService(),
        request_factory=build_request,
        signal_decision_service=SignalDecisionService(),
    )

    results = service.run_due_scans(
        datetime.now(timezone.utc)
    )

    assert len(results) == 1
    assert results[0]["symbol"] == "XAUUSD"
    assert results[0]["signal_event"] is not None
    assert results[0]["signal_event"].status == "SIGNAL"
    assert results[0]["signal_event"].direction == "BUY"


def test_proactive_scan_can_create_developing_event():
    watchlist = MarketWatchlistService(
        [
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    class FakeAnalysisService:
        def analyze(self, request):
            return {
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

    service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=FakeAnalysisService(),
        request_factory=build_request,
        signal_decision_service=SignalDecisionService(),
    )

    results = service.run_due_scans(
        datetime.now(timezone.utc)
    )

    assert len(results) == 1
    assert results[0]["signal_event"] is not None
    assert results[0]["signal_event"].status == "DEVELOPING"


def test_proactive_scan_returns_no_signal_for_waiting_analysis():
    watchlist = MarketWatchlistService(
        [
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
            )
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    class FakeAnalysisService:
        def analyze(self, request):
            return {
                "status": "WAIT",
                "opportunity_assessment": {
                    "direction": "BUY",
                },
                "ai_interpretation": {
                    "confidence": 0.4,
                    "summary": "Waiting for confirmation.",
                },
            }

    service = ProactiveScanService(
        scanner_service=scanner,
        analysis_service=FakeAnalysisService(),
        request_factory=build_request,
        signal_decision_service=SignalDecisionService(),
    )

    results = service.run_due_scans(
        datetime.now(timezone.utc)
    )

    assert len(results) == 1
    assert results[0]["signal_event"] is None
