import os

import requests
from dotenv import load_dotenv


load_dotenv()


class TwelveDataProvider:
    """
    Adapter for Twelve Data market-data APIs.

    The rest of Tradewisser should not need to know
    how Twelve Data works internally.
    """

    BASE_URL = "https://api.twelvedata.com"

    def __init__(self):
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "TWELVE_DATA_API_KEY is not configured."
            )

    def get_price(self, symbol: str) -> dict:
        """
        Retrieve the latest available price for an instrument.
        """

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError(
                "Symbol must not be empty."
            )

        response = requests.get(
            f"{self.BASE_URL}/price",
            params={
                "symbol": normalized_symbol,
                "apikey": self.api_key,
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if "status" in data and data["status"] == "error":
            raise ValueError(
                data.get(
                    "message",
                    "Twelve Data returned an error.",
                )
            )

        if "price" not in data:
            raise ValueError(
                "Twelve Data response did not contain a price."
            )

        return {
            "symbol": normalized_symbol,
            "price": float(data["price"]),
        }

    def get_candles(
        self,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 20,
    ) -> dict:
        """
        Retrieve OHLCV candles for an instrument.

        interval examples:

            1min
            5min
            15min
            30min
            1h
            4h
            1day

        outputsize controls the number of candles requested.
        """

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError(
                "Symbol must not be empty."
            )

        if outputsize <= 0:
            raise ValueError(
                "Output size must be greater than zero."
            )

        response = requests.get(
            f"{self.BASE_URL}/time_series",
            params={
                "symbol": normalized_symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": self.api_key,
            },
            timeout=15,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exception:
            if response.status_code == 429:
                raise RuntimeError(
                    "Twelve Data rate limit exceeded. "
                    "Please wait before requesting more market data."
                ) from exception

            raise

        data = response.json()

        if "status" in data and data["status"] == "error":
            raise ValueError(
                data.get(
                    "message",
                    "Twelve Data returned an error.",
                )
            )

        if "values" not in data:
            raise ValueError(
                "Twelve Data response did not contain candle data."
            )

        candles = []

        for candle in data["values"]:
            candles.append(
                {
                    "datetime": candle["datetime"],
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                    "volume": (
                        float(candle["volume"])
                        if "volume" in candle
                        else None
                    ),
                }
            )

        return {
            "symbol": normalized_symbol,
            "interval": interval,
            "candles": candles,
        }