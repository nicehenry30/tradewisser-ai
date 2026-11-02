from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EconomicDataProvider(ABC):
    """
    Provider interface for Forex economic and fundamental data.

    Concrete providers can later connect to services such as
    Trading Economics, Alpha Vantage, or another economic-data API.

    The provider supplies data.
    It does not make trading decisions.
    """

    @abstractmethod
    def get_currency_data(
        self,
        currency: str,
    ) -> dict[str, Any]:
        """
        Return the latest fundamental data available for a currency.
        """
        raise NotImplementedError

    @abstractmethod
    def get_upcoming_events(
        self,
        currencies: list[str],
    ) -> list[dict[str, Any]]:
        """
        Return upcoming economic events affecting the requested currencies.
        """
        raise NotImplementedError

    @abstractmethod
    def get_historical_data(
        self,
        currency: str,
        indicator: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Return historical observations for a fundamental indicator.
        """
        raise NotImplementedError