from app.strategy.reversal_family import ReversalFamilyDetector


def make_candle(index, low, high, close=None):
    if close is None:
        close = (low + high) / 2

    return {
        "datetime": f"2026-01-01T00:{index:02d}:00",
        "open": close,
        "high": high,
        "low": low,
        "close": close,
    }


def test_detector_rejects_invalid_direction():
    detector = ReversalFamilyDetector()

    candles = [
        make_candle(i, 99, 101)
        for i in range(10)
    ]

    try:
        detector.detect(candles, "neutral", timeframe="15m")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "direction must be" in str(exc)


def test_detector_rejects_invalid_timeframe():
    detector = ReversalFamilyDetector()

    candles = [
        make_candle(i, 99, 101)
        for i in range(10)
    ]

    try:
        detector.detect(candles, "bullish", timeframe="1h")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "timeframe must be" in str(exc)


def test_detector_returns_empty_for_insufficient_candles():
    detector = ReversalFamilyDetector()

    candles = [
        make_candle(i, 99, 101)
        for i in range(5)
    ]

    result = detector.detect(
        candles,
        "bullish",
        timeframe="15m",
    )

    assert result == []


def test_bullish_reversal_family_detects_forming_repeated_lows():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 101, 103),
        make_candle(1, 100, 102),
        make_candle(2, 98, 100),
        make_candle(3, 101, 103),
        make_candle(4, 102, 104),
        make_candle(5, 99, 102),
        make_candle(6, 98.1, 100),
        make_candle(7, 101, 103),
        make_candle(8, 102, 104),
        make_candle(9, 101, 103),
    ]

    candidates = detector.detect(
        candles,
        "bullish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bullish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2
    assert candidate.structure_broken is False
    assert candidate.pullback_detected is False
    assert candidate.entry_candidate is False
    assert candidate.state == "forming"


def test_bullish_reversal_family_detects_bos_waiting_for_pullback():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 101, 103),
        make_candle(1, 100, 102),
        make_candle(2, 98, 100),
        make_candle(3, 101, 103),
        make_candle(4, 102, 104),
        make_candle(5, 99, 102),
        make_candle(6, 98.1, 100),
        make_candle(7, 101, 103),
        make_candle(8, 102, 104),
        make_candle(9, 105, 106),
        make_candle(10, 107, 108),
        make_candle(11, 106, 107),
        make_candle(12, 105, 106),
    ]

    candidates = detector.detect(
        candles,
        "bullish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bullish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2
    assert candidate.structure_broken is True
    assert candidate.break_index is not None
    assert candidate.break_price is not None
    assert candidate.pullback_detected is False
    assert candidate.entry_candidate is False
    assert candidate.state == "broken_waiting_pullback"

def test_bullish_reversal_family_detects_pullback_ready():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 101, 103),
        make_candle(1, 100, 102),
        make_candle(2, 98, 100),
        make_candle(3, 101, 103),
        make_candle(4, 102, 104),
        make_candle(5, 99, 102),
        make_candle(6, 98.1, 100),
        make_candle(7, 101, 103),
        make_candle(8, 102, 104),

        # Bullish BOS above the intermediate structure.
        make_candle(9, 105, 106),
        make_candle(10, 107, 108),

        # Price pulls back into the broken 96-level structure zone
        # without reclaiming the protected high.
        make_candle(11, 98.2, 101),
        make_candle(12, 99, 102),
    ]

    candidates = detector.detect(
        candles,
        "bullish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bullish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2

    assert candidate.structure_broken is True
    assert candidate.break_index is not None
    assert candidate.break_price is not None

    assert candidate.pullback_detected is True
    assert candidate.pullback_index is not None

    assert candidate.entry_candidate is True
    assert candidate.valid is True
    assert candidate.state == "pullback_ready"

def test_bearish_reversal_family_detects_forming_repeated_highs():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 97, 99),
        make_candle(1, 98, 100),
        make_candle(2, 100, 102),
        make_candle(3, 97, 99),
        make_candle(4, 96, 98),
        make_candle(5, 99, 101),
        make_candle(6, 99.9, 102),
        make_candle(7, 97, 99),
        make_candle(8, 96, 98),
        make_candle(9, 97, 99),
    ]

    candidates = detector.detect(
        candles,
        "bearish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bearish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2

    assert candidate.structure_broken is False
    assert candidate.pullback_detected is False
    assert candidate.entry_candidate is False
    assert candidate.state == "forming"

def test_bearish_reversal_family_detects_bos_waiting_for_pullback():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 97, 99),
        make_candle(1, 98, 100),
        make_candle(2, 100, 102),
        make_candle(3, 97, 99),
        make_candle(4, 96, 98),
        make_candle(5, 99, 101),
        make_candle(6, 99.9, 102),
        make_candle(7, 97, 99),
        make_candle(8, 96, 98),

        # Bearish BOS below the intermediate structure.
        make_candle(9, 94, 95),
        make_candle(10, 92, 93),

        # Price continues lower without retesting the protected high.
        make_candle(11, 93, 94),
        make_candle(12, 92, 93),
    ]

    candidates = detector.detect(
        candles,
        "bearish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bearish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2

    assert candidate.structure_broken is True
    assert candidate.break_index is not None
    assert candidate.break_price is not None

    assert candidate.pullback_detected is False
    assert candidate.entry_candidate is False
    assert candidate.state == "broken_waiting_pullback"

def test_bearish_reversal_family_detects_pullback_ready():
    detector = ReversalFamilyDetector(
        swing_strength=2,
        test_tolerance_pct=0.002,
        pullback_tolerance_pct=0.0025,
    )

    candles = [
        make_candle(0, 97, 99),
        make_candle(1, 98, 100),
        make_candle(2, 100, 102),
        make_candle(3, 97, 99),
        make_candle(4, 96, 98),
        make_candle(5, 99, 101),
        make_candle(6, 99.9, 102),
        make_candle(7, 97, 99),
        make_candle(8, 96, 98),

        # Bearish BOS below the intermediate structure.
        make_candle(9, 94, 95),
        make_candle(10, 92, 93),

        # Price pulls back into the protected 102-level zone
        # without breaking the protected high.
        make_candle(11, 101.8, 102.0),
        make_candle(12, 98, 99),
    ]

    candidates = detector.detect(
        candles,
        "bearish",
        timeframe="15m",
    )

    assert candidates

    candidate = candidates[0]

    assert candidate.family == "repeated_level"
    assert candidate.direction == "bearish"
    assert candidate.timeframe == "15m"
    assert candidate.test_count >= 2

    assert candidate.structure_broken is True
    assert candidate.break_index is not None
    assert candidate.break_price is not None

    assert candidate.pullback_detected is True
    assert candidate.pullback_index is not None

    assert candidate.entry_candidate is True
    assert candidate.valid is True
    assert candidate.state == "pullback_ready"