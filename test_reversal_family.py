from app.services.market_data_service import MarketDataService
from app.strategy.reversal_family import ReversalFamilyDetector


market_data = MarketDataService()
detector = ReversalFamilyDetector()


for timeframe in ["15min", "5min"]:

    print("\n" + "=" * 70)
    print(f"TESTING XAU/USD — {timeframe}")
    print("=" * 70)

    data = market_data.get_candles(
        "XAU/USD",
        timeframe,
        100,
    )

    candles = data["candles"]

    print(f"Candles received: {len(candles)}")

    for direction in ["bullish", "bearish"]:

        results = detector.detect(
            candles,
            direction,
            "15m" if timeframe == "15min" else "5m",
        )

        print(f"\n{direction.upper()} CANDIDATES: {len(results)}")

        for number, result in enumerate(results, start=1):

            print(f"\nCandidate {number}")
            print("-" * 50)

            print("State:", result.state)
            print("Tests:", result.test_count)
            print("Structure level:", result.structure_level)
            print("Structure broken:", result.structure_broken)
            print("Break index:", result.break_index)
            print("Break price:", result.break_price)
            print("Pullback:", result.pullback_detected)
            print("Pullback index:", result.pullback_index)
            print("Entry candidate:", result.entry_candidate)
            print("Test points:", result.test_points)
            print("Reason:", result.reason)