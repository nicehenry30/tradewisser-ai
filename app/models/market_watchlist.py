from dataclasses import dataclass


@dataclass(frozen=True)
class MarketWatchlistItem:
    """
    Defines how an instrument should be monitored
    by Tradewisser's proactive scanner.

    This is monitoring configuration, not trading
    or risk specification.
    """

    symbol: str
    asset_class: str
    enabled: bool = True
    scan_interval_seconds: int = 300
    priority: int = 1

    def __post_init__(self):
        normalized_symbol = self.symbol.strip().upper()
        normalized_asset_class = self.asset_class.strip().lower()

        if not normalized_symbol:
            raise ValueError(
                "Watchlist symbol must not be empty."
            )

        if not normalized_asset_class:
            raise ValueError(
                "Asset class must not be empty."
            )

        if self.scan_interval_seconds <= 0:
            raise ValueError(
                "Scan interval must be greater than zero."
            )

        if self.priority <= 0:
            raise ValueError(
                "Priority must be greater than zero."
            )
