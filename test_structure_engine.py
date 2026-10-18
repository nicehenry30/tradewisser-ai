from app.services.structure_engine import StructureEngine


def make_candle(high, low):
    return {
        "open": low,
        "high": high,
        "low": low,
        "close": high,
    }


def test_repeated_fractal_structure():

    engine = StructureEngine(
        swing_strength=1
    )

    candles = [
        # Initial bullish structure
        make_candle(101, 99),
        make_candle(105, 100),
        make_candle(103, 98),
        make_candle(108, 102),
        make_candle(106, 101),
        make_candle(110, 104),

        # Break protected HL -> bearish CHOCH
        make_candle(107, 100),
        make_candle(103, 97),

        # New bearish structural low
        make_candle(101, 94),
        make_candle(99, 95),

        # Break new low -> bearish BOS
        make_candle(96, 91),

        # Bearish movement creates LH
        make_candle(97, 90),
        make_candle(100, 93),

        # Continue lower
        make_candle(98, 89),
        make_candle(95, 87),
        make_candle(96, 88),

        # Break LH -> bullish CHOCH
        make_candle(102, 92),

        # New bullish structural high
        make_candle(104, 95),
        make_candle(103, 93),
        make_candle(105, 94),

        # Break new high -> bullish BOS
        make_candle(103, 92),
        make_candle(106, 96),

        # Continue bullish
        make_candle(104, 95),
        make_candle(108, 99),
        make_candle(107, 97),
    ]

    result = engine.analyze(
        candles=candles,
        timeframe="15m",
    )

    print()
    print("=" * 70)
    print("REPEATED 15M FRACTAL STRUCTURE")
    print("=" * 70)

    print()
    print("Initial direction:")
    print(result["initial_direction"])

    print()
    print("Current direction:")
    print(result["current_direction"])

    print()
    print("Current state:")
    print(result["current_state"])

    print()
    print("Swing points:")

    for swing in result["swing_points"]:
        print(
            f"  index={swing['index']:>2} "
            f"{swing['point_type']:>4} "
            f"price={swing['price']}"
        )

    print()
    print("Events:")

    for event in result["events"]:
        print(
            f"  index={event['index']:>2} "
            f"{event['event_type']:>5} "
            f"direction={event['direction']:>7} "
            f"broken={event['broken_price']}"
        )

    print()
    print("Movements:")

    for number, movement in enumerate(
        result["movements"],
        start=1,
    ):
        print(
            f"  Movement {number}: "
            f"{movement['direction']} "
            f"-> {movement['status']}"
        )

    expected = [
        ("CHOCH", "bearish", 101.0),
        ("BOS", "bearish", 94.0),
        ("CHOCH", "bullish", 100.0),
        ("BOS", "bullish", 104.0),
    ]

    actual = [
        (
            event["event_type"],
            event["direction"],
            event["broken_price"],
        )
        for event in result["events"]
    ]

    assert actual == expected, (
        f"\nExpected:\n{expected}\n"
        f"\nActual:\n{actual}"
    )

    assert result["initial_direction"] == "bullish"
    assert result["current_direction"] == "bullish"

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_repeated_fractal_structure()