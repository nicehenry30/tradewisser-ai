from datetime import datetime, timedelta

from app.services.market_data_service import MarketDataService


def candle_map(candles):
    return {
        datetime.fromisoformat(candle["datetime"]): candle
        for candle in candles
    }


def aggregate_candles(children):
    """
    Aggregate lower-timeframe candles into one higher-timeframe candle.

    Assumes timestamps represent the beginning of each candle.
    """
    ordered = sorted(
        children,
        key=lambda candle: datetime.fromisoformat(candle["datetime"]),
    )

    return {
        "open": float(ordered[0]["open"]),
        "high": max(float(c["high"]) for c in ordered),
        "low": min(float(c["low"]) for c in ordered),
        "close": float(ordered[-1]["close"]),
    }


def compare_candles(actual, expected):
    fields = ["open", "high", "low", "close"]

    differences = {}

    for field in fields:
        actual_value = float(actual[field])
        expected_value = float(expected[field])

        difference = abs(actual_value - expected_value)

        if difference > 0.00000001:
            differences[field] = {
                "actual": actual_value,
                "expected": expected_value,
                "difference": difference,
            }

    return differences


def check_parent_from_30m(
    thirty_minute_candles,
    parent_candles,
    child_count,
    parent_name,
):
    thirty_map = candle_map(thirty_minute_candles)

    checked = 0
    matched = 0
    mismatches = []

    for parent in parent_candles:
        parent_time = datetime.fromisoformat(
            parent["datetime"]
        )

        children = []

        for offset in range(child_count):
            child_time = parent_time + timedelta(
                minutes=30 * offset
            )

            child = thirty_map.get(child_time)

            if child is None:
                break

            children.append(child)

        if len(children) != child_count:
            continue

        expected = aggregate_candles(children)

        differences = compare_candles(
            parent,
            expected,
        )

        checked += 1

        if not differences:
            matched += 1
        else:
            mismatches.append(
                {
                    "parent": parent_time,
                    "differences": differences,
                }
            )

    print()
    print("=" * 80)
    print(f"{parent_name} CONSISTENCY TEST")
    print("=" * 80)

    print(f"Complete parent candles checked: {checked}")
    print(f"Correctly aggregated:             {matched}")
    print(f"Mismatches:                       {len(mismatches)}")

    if mismatches:
        print()
        print("FIRST MISMATCHES")
        print("-" * 80)

        for mismatch in mismatches[:5]:
            print(
                mismatch["parent"].isoformat()
            )

            for field, values in mismatch["differences"].items():
                print(
                    f"  {field}: "
                    f"actual={values['actual']} "
                    f"expected={values['expected']} "
                    f"difference={values['difference']}"
                )

    if checked > 0:
        percentage = (
            matched / checked
        ) * 100

        print()
        print(
            f"Consistency: {percentage:.2f}%"
        )


def main():
    market_data = MarketDataService()

    symbol = "XAU/USD"

    print("=" * 80)
    print("TRADewisser MULTI-TIMEFRAME MARKET DATA CONSISTENCY TEST")
    print("=" * 80)
    print()
    print(f"Symbol: {symbol}")
    print()
    print("Downloading:")
    print("  30M candles...")
    thirty_minute = market_data.get_candles(
        symbol,
        "30min",
        200,
    )

    print("  1H candles...")
    one_hour = market_data.get_candles(
        symbol,
        "1h",
        100,
    )

    print("  4H candles...")
    four_hour = market_data.get_candles(
        symbol,
        "4h",
        50,
    )

    print()
    print("Downloaded:")
    print(
        f"  30M: {len(thirty_minute['candles'])} candles"
    )
    print(
        f"  1H:  {len(one_hour['candles'])} candles"
    )
    print(
        f"  4H:  {len(four_hour['candles'])} candles"
    )

    check_parent_from_30m(
        thirty_minute["candles"],
        one_hour["candles"],
        child_count=2,
        parent_name="1H FROM 30M",
    )

    check_parent_from_30m(
        thirty_minute["candles"],
        four_hour["candles"],
        child_count=8,
        parent_name="4H FROM 30M",
    )

    print()
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()
    print(
        "If the consistency is close to 100%, the higher-timeframe "
        "candles are internally consistent with the 30M feed."
    )
    print()
    print(
        "If there are significant mismatches, we need to investigate "
        "the XAU/USD data feed before trusting higher-timeframe analysis."
    )


if __name__ == "__main__":
    main()