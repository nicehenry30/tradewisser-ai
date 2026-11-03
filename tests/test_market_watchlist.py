import pytest

from app.models.market_watchlist import MarketWatchlistItem


def test_creates_valid_watchlist_item():
    item = MarketWatchlistItem(
        symbol="XAUUSD",
        asset_class="metals",
    )

    assert item.symbol == "XAUUSD"
    assert item.asset_class == "metals"
    assert item.enabled is True
    assert item.scan_interval_seconds == 300
    assert item.priority == 1


def test_accepts_custom_monitoring_configuration():
    item = MarketWatchlistItem(
        symbol="EURUSD",
        asset_class="forex",
        enabled=False,
        scan_interval_seconds=60,
        priority=2,
    )

    assert item.symbol == "EURUSD"
    assert item.asset_class == "forex"
    assert item.enabled is False
    assert item.scan_interval_seconds == 60
    assert item.priority == 2


def test_rejects_empty_symbol():
    with pytest.raises(ValueError, match="Watchlist symbol must not be empty"):
        MarketWatchlistItem(
            symbol="",
            asset_class="forex",
        )


def test_rejects_empty_asset_class():
    with pytest.raises(ValueError, match="Asset class must not be empty"):
        MarketWatchlistItem(
            symbol="EURUSD",
            asset_class="",
        )


def test_rejects_invalid_scan_interval():
    with pytest.raises(
        ValueError,
        match="Scan interval must be greater than zero",
    ):
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            scan_interval_seconds=0,
        )


def test_rejects_invalid_priority():
    with pytest.raises(
        ValueError,
        match="Priority must be greater than zero",
    ):
        MarketWatchlistItem(
            symbol="XAUUSD",
            asset_class="metals",
            priority=0,
        )


def test_watchlist_item_is_immutable():
    item = MarketWatchlistItem(
        symbol="XAUUSD",
        asset_class="metals",
    )

    with pytest.raises(AttributeError):
        item.enabled = False
