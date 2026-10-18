from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MarketDataValidationResult:
    """
    Result of validating a market-data candle series.

    The validator checks structural data integrity.
    It does not decide whether the market is bullish,
    bearish, ranging, or tradeable.
    """

    valid: bool
    symbol: str
    interval: str
    candle_count: int
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "symbol": self.symbol,
            "interval": self.interval,
            "candle_count": self.candle_count,
            "reasons": self.reasons,
            "warnings": self.warnings,
        }


class MarketDataValidator:
    """
    Deterministic validation layer for market OHLC data.

    This class validates data integrity only.

    It does NOT reject a market simply because:
        - volatility is low
        - candles are small
        - price is consolidating
        - highs/lows are close together

    Those can all be legitimate market conditions.
    """

    EXPECTED_INTERVAL_MINUTES = {
        "1min": 1,
        "5min": 5,
        "15min": 15,
        "30min": 30,
        "1h": 60,
        "4h": 240,
        "1day": 1440,
    }

    def validate(
        self,
        symbol: str,
        interval: str,
        candles: list[dict[str, Any]],
    ) -> MarketDataValidationResult:
        reasons: list[str] = []
        warnings: list[str] = []

        normalized_symbol = symbol.strip().upper()
        normalized_interval = interval.strip().lower()

        if not normalized_symbol:
            reasons.append("empty_symbol")

        if normalized_interval not in self.EXPECTED_INTERVAL_MINUTES:
            reasons.append(
                f"unsupported_interval:{normalized_interval}"
            )

        if not candles:
            reasons.append("no_candles")

            return MarketDataValidationResult(
                valid=False,
                symbol=normalized_symbol,
                interval=normalized_interval,
                candle_count=0,
                reasons=reasons,
                warnings=warnings,
            )

        self._validate_ohlc(
            candles,
            reasons,
        )

        self._validate_timestamps(
            candles,
            normalized_interval,
            reasons,
        )

        self._detect_stale_candles(
            candles,
            warnings,
        )

        return MarketDataValidationResult(
            valid=len(reasons) == 0,
            symbol=normalized_symbol,
            interval=normalized_interval,
            candle_count=len(candles),
            reasons=reasons,
            warnings=warnings,
        )

    def _validate_ohlc(
        self,
        candles: list[dict[str, Any]],
        reasons: list[str],
    ) -> None:
        required_fields = (
            "datetime",
            "open",
            "high",
            "low",
            "close",
        )

        for index, candle in enumerate(candles):
            for field_name in required_fields:
                if field_name not in candle:
                    reasons.append(
                        f"missing_field:{index}:{field_name}"
                    )

            if any(
                field_name not in candle
                for field_name in required_fields
            ):
                continue

            try:
                open_price = float(candle["open"])
                high_price = float(candle["high"])
                low_price = float(candle["low"])
                close_price = float(candle["close"])
            except (TypeError, ValueError):
                reasons.append(
                    f"non_numeric_ohlc:{index}"
                )
                continue

            if high_price < low_price:
                reasons.append(
                    f"high_below_low:{index}"
                )

            if high_price < max(
                open_price,
                close_price,
            ):
                reasons.append(
                    f"high_below_open_or_close:{index}"
                )

            if low_price > min(
                open_price,
                close_price,
            ):
                reasons.append(
                    f"low_above_open_or_close:{index}"
                )

    def _validate_timestamps(
        self,
        candles: list[dict[str, Any]],
        interval: str,
        reasons: list[str],
    ) -> None:
        expected_minutes = (
            self.EXPECTED_INTERVAL_MINUTES.get(
                interval
            )
        )

        if expected_minutes is None:
            return

        parsed_timestamps: list[datetime] = []

        for index, candle in enumerate(candles):
            try:
                timestamp = datetime.fromisoformat(
                    str(candle["datetime"])
                )

                parsed_timestamps.append(
                    timestamp
                )

            except (
                KeyError,
                ValueError,
                TypeError,
            ):
                reasons.append(
                    f"invalid_timestamp:{index}"
                )

        if len(parsed_timestamps) < 2:
            return

        for index in range(
            len(parsed_timestamps) - 1
        ):
            current = parsed_timestamps[index]
            previous = parsed_timestamps[index + 1]

            difference_minutes = (
                current - previous
            ).total_seconds() / 60

            if difference_minutes != expected_minutes:
                reasons.append(
                    "unexpected_interval_spacing:"
                    f"{index}:"
                    f"expected_{expected_minutes}m:"
                    f"actual_{difference_minutes:g}m"
                )

    def _detect_stale_candles(
        self,
        candles: list[dict[str, Any]],
        warnings: list[str],
    ) -> None:
        """
        Detects identical recent closes.

        This is only a warning.

        Identical closes can occur during legitimate
        low-volatility or consolidating market conditions.
        """

        if len(candles) < 3:
            return

        recent = candles[:3]

        closes = [
            float(candle["close"])
            for candle in recent
        ]

        if len(set(closes)) == 1:
            warnings.append(
                "recent_closes_identical"
            )