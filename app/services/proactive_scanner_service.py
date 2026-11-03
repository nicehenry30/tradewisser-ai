from datetime import datetime, timedelta

from app.models.market_watchlist import MarketWatchlistItem
from app.services.market_watchlist_service import MarketWatchlistService


class ProactiveScannerService:
    """
    Determines which watchlist instruments are due for analysis.

    This service is responsible only for scan scheduling.
    It does not analyze markets or make trading decisions.
    """

    def __init__(
        self,
        watchlist_service: MarketWatchlistService,
    ):
        self._watchlist_service = watchlist_service
        self._last_scanned_at: dict[str, datetime] = {}

    def get_due_items(
        self,
        now: datetime,
    ) -> list[MarketWatchlistItem]:
        """
        Return enabled instruments whose scan interval has elapsed.

        Instruments that have never been scanned are immediately due.
        """
        due_items: list[MarketWatchlistItem] = []

        for item in self._watchlist_service.list_enabled_items():
            last_scanned = self._last_scanned_at.get(
                item.symbol.strip().upper()
            )

            if last_scanned is None:
                due_items.append(item)
                continue

            next_scan_time = (
                last_scanned
                + timedelta(
                    seconds=item.scan_interval_seconds
                )
            )

            if now >= next_scan_time:
                due_items.append(item)

        return due_items

    def mark_scanned(
        self,
        symbol: str,
        scanned_at: datetime,
    ) -> None:
        """
        Record the time an instrument was scanned.
        """
        normalized_symbol = symbol.strip().upper()

        item = self._watchlist_service.get_item(
            normalized_symbol
        )

        if item is None:
            raise ValueError(
                f"Instrument '{normalized_symbol}' "
                "is not on the watchlist"
            )

        self._last_scanned_at[normalized_symbol] = scanned_at
