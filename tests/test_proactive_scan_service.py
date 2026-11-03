from datetime import datetime, timedelta
from unittest.mock import Mock

from app.models.analysis_request import AnalysisRequest
from app.models.market_watchlist import MarketWatchlistItem
from app.services.active_signal_registry import ActiveSignalRegistry
from app.services.market_watchlist_service import MarketWatchlistService
from app.services.proactive_scan_service import ProactiveScanService
from app.services.proactive_scanner_service import ProactiveScannerService
from app.services.signal_decision_service import SignalDecisionService
from app.services.signal_lifecycle_coordinator import (
    SignalLifecycleCoordinator,
)


def build_services(items):
    watchlist_service = MarketWatchlistService(items)

    scanner_service = ProactiveScannerService(
        watchlist_service
    )

    analysis_service = Mock()

    request_factory = Mock(
        side_effect=lambda symbol: AnalysisRequest(
            symbol=symbol,
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    return (
        scanner_service,
        analysis_service,
        request_factory,
    )


def test_due_instrument_is_sent_to_analysis():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            scan_interval_seconds=300,
            priority=1,
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    analysis_service.analyze.return_value = {
        "status": "WAIT",
        "symbol": "XAUUSD",
    }

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    results = service.run_due_scans(now)

    request_factory.assert_called_once_with(
        "XAUUSD"
    )

    analysis_service.analyze.assert_called_once_with(
        AnalysisRequest(
            symbol="XAUUSD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert results == [
        {
            "symbol": "XAUUSD",
            "result": {
                "status": "WAIT",
                "symbol": "XAUUSD",
            },
            "signal_event": None,
            "signal_id": None,
            "lifecycle": None,
        }
    ]


def test_disabled_instrument_is_not_analyzed():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            enabled=False,
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    results = service.run_due_scans(now)

    analysis_service.analyze.assert_not_called()
    request_factory.assert_not_called()

    assert results == []


def test_non_due_instrument_is_not_analyzed():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            scan_interval_seconds=300,
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    first_scan = datetime(2026, 11, 3, 12, 0, 0)

    analysis_service.analyze.return_value = {
        "status": "WAIT"
    }

    service.run_due_scans(first_scan)

    analysis_service.reset_mock()
    request_factory.reset_mock()

    second_scan = first_scan + timedelta(
        seconds=100
    )

    results = service.run_due_scans(second_scan)

    analysis_service.analyze.assert_not_called()
    request_factory.assert_not_called()

    assert results == []


def test_scan_time_is_recorded_after_analysis():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    analysis_service.analyze.return_value = {
        "status": "SIGNAL"
    }

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    service.run_due_scans(now)

    assert analysis_service.analyze.call_count == 1

    later = now + timedelta(seconds=100)

    results = service.run_due_scans(later)

    assert analysis_service.analyze.call_count == 1
    assert results == []


def test_analysis_result_is_returned_to_caller():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    expected_result = {
        "status": "AUTHORIZED",
        "symbol": "XAUUSD",
    }

    analysis_service.analyze.return_value = expected_result

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    results = service.run_due_scans(now)

    assert results[0]["result"] == expected_result


def test_analysis_failure_does_not_become_signal():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    analysis_service.analyze.side_effect = RuntimeError(
        "Market data unavailable"
    )

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    results = service.run_due_scans(now)

    assert len(results) == 1
    assert results[0]["symbol"] == "XAUUSD"
    assert results[0]["result"]["status"] == "ERROR"
    assert "Market data unavailable" in (
        results[0]["result"]["error"]
    )


def test_signal_progression_preserves_identity():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            scan_interval_seconds=1,
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    analysis_results = [
        {
            "status": "WAIT",
            "opportunity_assessment": {
                "direction": "BUY",
                "opportunity": "POTENTIAL",
            },
            "ai_interpretation": {
                "confidence": 0.65,
                "summary": "Bullish opportunity developing.",
            },
            "five_minute_confirmation": {
                "confirmed": False,
            },
        },
        {
            "status": "WAIT",
            "opportunity_assessment": {
                "direction": "BUY",
                "opportunity": "POTENTIAL",
            },
            "ai_interpretation": {
                "confidence": 0.78,
                "summary": "Lower timeframe confirmation supports the setup.",
            },
            "five_minute_confirmation": {
                "confirmed": True,
            },
        },
        {
            "status": "AUTHORIZED",
            "opportunity_assessment": {
                "direction": "BUY",
                "opportunity": "VALID",
            },
            "ai_interpretation": {
                "confidence": 0.91,
                "summary": "Setup passed confirmation and risk controls.",
            },
        },
    ]

    analysis_service.analyze.side_effect = analysis_results

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
    )

    first_scan = datetime(2026, 11, 3, 12, 0, 0)

    first_results = service.run_due_scans(first_scan)

    assert first_results[0]["signal_event"].status == "DEVELOPING"
    assert first_results[0]["signal_id"] == "XAUUSD-BUY-001"
    assert first_results[0]["lifecycle"].status == "NEW"

    second_scan = first_scan + timedelta(seconds=1)

    second_results = service.run_due_scans(second_scan)

    assert second_results[0]["signal_event"].status == "CONFIRMED"
    assert second_results[0]["signal_id"] == "XAUUSD-BUY-001"
    assert second_results[0]["lifecycle"].status == "NEW"

    third_scan = second_scan + timedelta(seconds=1)

    third_results = service.run_due_scans(third_scan)

    assert third_results[0]["signal_event"].status == "SIGNAL"
    assert third_results[0]["signal_id"] == "XAUUSD-BUY-001"
    assert third_results[0]["lifecycle"].status == "ACTIVE"


def test_signal_lifecycle_coordinator_can_be_injected():
    items = [
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
        )
    ]

    (
        scanner_service,
        analysis_service,
        request_factory,
    ) = build_services(items)

    analysis_service.analyze.return_value = {
        "status": "AUTHORIZED",
        "opportunity_assessment": {
            "direction": "BUY",
            "opportunity": "VALID",
        },
        "ai_interpretation": {
            "confidence": 0.91,
            "summary": "Setup passed confirmation and risk controls.",
        },
    }

    registry = ActiveSignalRegistry()

    lifecycle_coordinator = SignalLifecycleCoordinator(
        registry
    )

    service = ProactiveScanService(
        scanner_service=scanner_service,
        analysis_service=analysis_service,
        request_factory=request_factory,
        signal_decision_service=SignalDecisionService(),
        signal_registry=registry,
        lifecycle_coordinator=lifecycle_coordinator,
    )

    now = datetime(2026, 11, 3, 12, 0, 0)

    results = service.run_due_scans(now)

    assert results[0]["signal_id"] == "XAUUSD-BUY-001"
    assert results[0]["lifecycle"].status == "ACTIVE"

    stored_lifecycle = registry.get_lifecycle(
        "XAUUSD-BUY-001"
    )

    assert stored_lifecycle is not None
    assert stored_lifecycle.status == "ACTIVE"