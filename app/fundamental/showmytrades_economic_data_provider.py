from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.fundamental.economic_data_provider import EconomicDataProvider


class ShowMyTradesEconomicDataProvider(EconomicDataProvider):
    """
    Free ShowMyTrades economic-calendar provider.

    This provider requires no API key.

    Current responsibilities:
        - Fetch upcoming economic-calendar events.
        - Filter events by currency, impact, and days.
        - Expose event data through the EconomicDataProvider contract.

    Important:
        ShowMyTrades currently provides economic-calendar data rather
        than the complete macroeconomic snapshot required by the
        FundamentalAnalysisEngine.

        Therefore get_currency_data() deliberately returns neutral,
        unavailable indicators rather than inventing economic values.
    """

    BASE_URL = (
        "https://showmytrades.com/api/public/calendar/v1"
    )

    SUPPORTED_CURRENCIES = {
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "AUD",
        "NZD",
        "CAD",
        "CHF",
        "CNY",
    }

    def __init__(
        self,
        timeout: float = 10.0,
    ):
        self.timeout = timeout

    def get_currency_data(
        self,
        currency: str,
    ) -> dict[str, Any]:
        """
        Return the currently available fundamental snapshot.

        ShowMyTrades' public endpoint is an economic calendar,
        not a complete historical macroeconomic indicator API.

        We therefore explicitly mark the unavailable indicators
        instead of fabricating values.
        """

        currency = currency.strip().upper()

        return {
            "currency": currency,
            "inflation_bias": "neutral",
            "growth_bias": "neutral",
            "employment_bias": "neutral",
            "monetary_policy_bias": "neutral",
            "interest_rate_bias": "neutral",
            "economic_surprise_bias": "neutral",
            "confidence": 0.0,
            "key_drivers": [],
            "risks": [
                "macro_indicator_data_unavailable_from_current_provider"
            ],
            "available_indicators": [],
        }

    def get_upcoming_events(
        self,
        currencies: list[str],
    ) -> list[dict[str, Any]]:
        """
        Fetch upcoming economic-calendar events.

        The public ShowMyTrades endpoint requires no API key.
        """

        normalized_currencies = [
            currency.strip().upper()
            for currency in currencies
            if currency.strip()
        ]

        unsupported = [
            currency
            for currency in normalized_currencies
            if currency not in self.SUPPORTED_CURRENCIES
        ]

        if unsupported:
            raise ValueError(
                "Unsupported currency(s): "
                + ", ".join(unsupported)
            )

        params = {
            "currency": ",".join(normalized_currencies),
            "impact": "high,medium",
            "days": "7",
            "format": "json",
        }

        url = f"{self.BASE_URL}?{urlencode(params)}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Tradewisser-AI/1.0",
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                status = getattr(
                    response,
                    "status",
                    200,
                )

                if status != 200:
                    raise RuntimeError(
                        "ShowMyTrades returned HTTP "
                        f"{status}."
                    )

                payload = json.loads(
                    response.read().decode("utf-8")
                )

        except Exception as exc:
            raise RuntimeError(
                "Failed to fetch economic calendar "
                "from ShowMyTrades."
            ) from exc

        events = payload.get("events", [])

        if not isinstance(events, list):
            raise RuntimeError(
                "ShowMyTrades returned an invalid "
                "economic-calendar response."
            )

        return [
            self._normalize_event(event)
            for event in events
            if isinstance(event, dict)
        ]

    def get_historical_data(
        self,
        currency: str,
        indicator: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        ShowMyTrades' current public calendar endpoint does not
        provide historical macroeconomic indicator series.

        Return an empty result rather than fabricating history.
        """

        return []

    @staticmethod
    def _normalize_event(
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize the external API response into the internal
        economic-event contract.
        """

        return {
            "timestamp": event.get("ts"),
            "datetime": event.get("time"),
            "currency": event.get("currency"),
            "importance": event.get("impact"),
            "title": event.get("title"),
            "forecast": event.get("forecast"),
            "previous": event.get("previous"),
            "actual": event.get("actual"),
        }