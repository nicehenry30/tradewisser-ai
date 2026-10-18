from app.services.twelve_data_provider import TwelveDataProvider


class MarketDataService:
    """
    Application-level market data service.

    Tradewisser uses this service instead of communicating
    directly with a specific market-data provider.

    This keeps the AI layer independent from Twelve Data.
    """

    def __init__(self):
        self.provider = TwelveDataProvider()

    def get_price(self, symbol: str) -> dict:
        """
        Get the latest available market price for a symbol.
        """

        return self.provider.get_price(symbol)

    def get_candles(
        self,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 20,
    ) -> dict:
        """
        Get OHLCV candles for a symbol.

        The provider-specific implementation remains hidden
        behind the market-data service.
        """

        return self.provider.get_candles(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
        )