from __future__ import annotations

from typing import Any

from app.fundamental.economic_data_provider import (
    EconomicDataProvider,
)


class MockEconomicDataProvider(EconomicDataProvider):
    """
    Deterministic economic-data provider used for development
    and testing before connecting a live API.
    """

    def __init__(
        self,
        currency_data: dict[str, dict[str, Any]] | None = None,
        upcoming_events: list[dict[str, Any]] | None = None,
        historical_data: dict[
            tuple[str, str],
            list[dict[str, Any]],
        ] | None = None,
    ):
        self.currency_data = currency_data or {}
        self.upcoming_events = upcoming_events or []
        self.historical_data = historical_data or {}

    def get_currency_data(
        self,
        currency: str,
    ) -> dict[str, Any]:
        currency = currency.upper().strip()

        return dict(
            self.currency_data.get(
                currency,
                {
                    "currency": currency,
                },
            )
        )

    def get_upcoming_events(
        self,
        currencies: list[str],
    ) -> list[dict[str, Any]]:
        requested = {
            currency.upper().strip()
            for currency in currencies
        }

        return [
            dict(event)
            for event in self.upcoming_events
            if str(event.get("currency", "")).upper()
            in requested
        ]

    def get_historical_data(
        self,
        currency: str,
        indicator: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        key = (
            currency.upper().strip(),
            indicator,
        )

        observations = self.historical_data.get(
            key,
            [],
        )

        return [
            dict(observation)
            for observation in observations[:limit]
        ]