from app.models.market_watchlist import MarketWatchlistItem


class MarketWatchlistService:
    """
    Manages Tradewisser's proactive market watchlist.

    This service controls monitoring configuration only.
    It does not make trading decisions, calculate risk,
    or authorize trades.
    """

    def __init__(
        self,
        items: list[MarketWatchlistItem] | None = None,
    ):
        if items is None:
            items = [
                MarketWatchlistItem(
                    symbol="XAUUSD",
                    asset_class="metals",
                    enabled=True,
                    scan_interval_seconds=300,
                    priority=1,
                ),
            ]

        self._items = list(items)

        self._validate_unique_symbols()

    def _validate_unique_symbols(self) -> None:
        seen_symbols: set[str] = set()

        for item in self._items:
            normalized_symbol = item.symbol.strip().upper()

            if normalized_symbol in seen_symbols:
                raise ValueError(
                    f"Duplicate watchlist symbol: "
                    f"{normalized_symbol}"
                )

            seen_symbols.add(normalized_symbol)

    def list_items(self) -> list[MarketWatchlistItem]:
        """
        Return all configured watchlist items.
        """
        return list(self._items)

    def list_enabled_items(self) -> list[MarketWatchlistItem]:
        """
        Return enabled instruments ordered by priority.
        """
        return sorted(
            (
                item
                for item in self._items
                if item.enabled
            ),
            key=lambda item: item.priority,
        )

    def get_item(
        self,
        symbol: str,
    ) -> MarketWatchlistItem | None:
        """
        Find a watchlist item by symbol.

        Symbol lookup is case-insensitive.
        """
        normalized_symbol = symbol.strip().upper()

        for item in self._items:
            if item.symbol.strip().upper() == normalized_symbol:
                return item

        return None
