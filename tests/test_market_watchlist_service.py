import pytest

from app.models.market_watchlist import MarketWatchlistItem
from app.services.market_watchlist_service import MarketWatchlistService


def test_returns_default_watchlist():
    service = MarketWatchlistService()

    items = service.list_items()

    assert len(items) > 0
    assert all(
        isinstance(item, MarketWatchlistItem)
        for item in items
    )


def test_default_watchlist_contains_xauusd():
    service = MarketWatchlistService()

    item = service.get_item("XAUUSD")

    assert item.symbol == "XAUUSD"
    assert item.asset_class == "metals"


def test_get_item_is_case_insensitive():
    service = MarketWatchlistService()

    item = service.get_item("xauusd")

    assert item.symbol == "XAUUSD"


def test_returns_only_enabled_items():
    service = MarketWatchlistService(
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

    enabled_items = service.list_enabled_items()

    assert len(enabled_items) == 1
    assert enabled_items[0].symbol == "XAUUSD"


def test_unknown_instrument_returns_none():
    service = MarketWatchlistService()

    assert service.get_item("UNKNOWN") is None


def test_list_enabled_items_is_sorted_by_priority():
    service = MarketWatchlistService(
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

    items = service.list_enabled_items()

    assert [item.symbol for item in items] == [
        "XAUUSD",
        "GBPUSD",
        "EURUSD",
    ]


def test_rejects_duplicate_symbols():
    with pytest.raises(
        ValueError,
        match="Duplicate watchlist symbol",
    ):
        MarketWatchlistService(
            items=[
                MarketWatchlistItem(
                    symbol="XAUUSD",
                    asset_class="metals",
                ),
                MarketWatchlistItem(
                    symbol="xauusd",
                    asset_class="metals",
                ),
            ]
        )
