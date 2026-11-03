from datetime import datetime, timedelta

from app.models.market_watchlist import MarketWatchlistItem
from app.services.market_watchlist_service import MarketWatchlistService
from app.services.proactive_scanner_service import ProactiveScannerService


def test_scans_enabled_instruments():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                enabled=True,
            ),
            MarketWatchlistItem(
                symbol="EURUSD",
                asset_class="forex",
                enabled=True,
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    due_items = scanner.get_due_items(
        now=datetime(2026, 11, 3, 12, 0, 0)
    )

    assert [item.symbol for item in due_items] == [
        "XAUUSD",
        "EURUSD",
    ]


def test_skips_disabled_instruments():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                enabled=True,
            ),
            MarketWatchlistItem(
                symbol="EURUSD",
                asset_class="forex",
                enabled=False,
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    due_items = scanner.get_due_items(
        now=datetime(2026, 11, 3, 12, 0, 0)
    )

    assert [item.symbol for item in due_items] == [
        "XAUUSD",
    ]


def test_higher_priority_items_are_scanned_first():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="EURUSD",
                asset_class="forex",
                priority=3,
            ),
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                priority=1,
            ),
            MarketWatchlistItem(
                symbol="GBPUSD",
                asset_class="forex",
                priority=2,
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    due_items = scanner.get_due_items(
        now=datetime(2026, 11, 3, 12, 0, 0)
    )

    assert [item.symbol for item in due_items] == [
        "XAUUSD",
        "GBPUSD",
        "EURUSD",
    ]


def test_item_is_not_due_before_scan_interval_expires():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                scan_interval_seconds=300,
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    first_scan = datetime(2026, 11, 3, 12, 0, 0)

    scanner.mark_scanned(
        "XAUUSD",
        first_scan,
    )

    due_items = scanner.get_due_items(
        now=first_scan + timedelta(seconds=299)
    )

    assert due_items == []


def test_item_becomes_due_after_scan_interval_expires():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
                scan_interval_seconds=300,
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    first_scan = datetime(2026, 11, 3, 12, 0, 0)

    scanner.mark_scanned(
        "XAUUSD",
        first_scan,
    )

    due_items = scanner.get_due_items(
        now=first_scan + timedelta(seconds=300)
    )

    assert [item.symbol for item in due_items] == [
        "XAUUSD",
    ]


def test_unknown_symbol_cannot_be_marked_as_scanned():
    watchlist = MarketWatchlistService(
        items=[
            MarketWatchlistItem(
                symbol="XAUUSD",
                asset_class="metals",
            ),
        ]
    )

    scanner = ProactiveScannerService(watchlist)

    try:
        scanner.mark_scanned(
            "UNKNOWN",
            datetime(2026, 11, 3, 12, 0, 0),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Instrument 'UNKNOWN' is not on the watchlist"
