from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ReversalFamilyCandidate:
    family: str
    direction: str
    timeframe: str | None

    test_count: int
    test_points: list[dict[str, Any]]

    structure_level: float | None
    structure_broken: bool
    break_index: int | None
    break_price: float | None

    pullback_detected: bool
    pullback_index: int | None

    entry_candidate: bool
    valid: bool

    state: str
    reason: str

    detection_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "direction": self.direction,
            "timeframe": self.timeframe,
            "test_count": self.test_count,
            "test_points": self.test_points,
            "structure_level": self.structure_level,
            "structure_broken": self.structure_broken,
            "break_index": self.break_index,
            "break_price": self.break_price,
            "pullback_detected": self.pullback_detected,
            "pullback_index": self.pullback_index,
            "entry_candidate": self.entry_candidate,
            "valid": self.valid,
            "state": self.state,
            "reason": self.reason,
            "detection_notes": self.detection_notes,
        }


class ReversalFamilyDetector:
    """
    Detects the user's repeated-level reversal family.

    Bullish:
        repeated lows
            ↓
        protected support
            ↓
        break of structure
            ↓
        pullback / retest
            ↓
        entry candidate

    Bearish is the mirror image.

    This detector is deliberately recall-oriented.
    It finds candidates; later confirmation and entry layers decide
    whether the setup is actually tradable.

    Tolerances are configurable research parameters until the user
    defines exact numerical thresholds.
    """

    ALLOWED_TIMEFRAMES = {"15m", "5m", "1m"}

    def __init__(
        self,
        swing_strength: int = 2,
        test_tolerance_pct: float = 0.0015,
        pullback_tolerance_pct: float = 0.0025,
    ):
        if swing_strength < 1:
            raise ValueError("swing_strength must be at least 1.")

        if test_tolerance_pct <= 0:
            raise ValueError(
                "test_tolerance_pct must be greater than 0."
            )

        if pullback_tolerance_pct <= 0:
            raise ValueError(
                "pullback_tolerance_pct must be greater than 0."
            )

        self.swing_strength = swing_strength
        self.test_tolerance_pct = test_tolerance_pct
        self.pullback_tolerance_pct = pullback_tolerance_pct

    def detect(
        self,
        candles: list[dict[str, Any]],
        direction: str,
        timeframe: str | None = None,
    ) -> list[ReversalFamilyCandidate]:

        direction = direction.lower().strip()

        if direction not in {"bullish", "bearish"}:
            raise ValueError(
                "direction must be 'bullish' or 'bearish'."
            )

        if (
            timeframe is not None
            and timeframe not in self.ALLOWED_TIMEFRAMES
        ):
            raise ValueError(
                "timeframe must be one of: 15m, 5m, 1m."
            )

        normalized = self._normalize_candles(candles)

        minimum_candles = self.swing_strength * 2 + 5

        if len(normalized) < minimum_candles:
            return []

        swings = self._find_swings(normalized)

        if direction == "bullish":
            return self._detect_bullish_repeated_tests(
                normalized,
                swings["lows"],
                swings["highs"],
                timeframe,
            )

        return self._detect_bearish_repeated_tests(
            normalized,
            swings["highs"],
            swings["lows"],
            timeframe,
        )

    # ---------------------------------------------------------
    # Candle preparation
    # ---------------------------------------------------------

    def _normalize_candles(
        self,
        candles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        normalized = []

        for candle in candles:
            normalized.append(
                {
                    "datetime": candle.get("datetime"),
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                }
            )

        # Always analyze market data chronologically:
        # oldest candle -> newest candle.
        normalized.sort(
            key=lambda candle: candle["datetime"]
        )

        for index, candle in enumerate(normalized):
            candle["index"] = index

        return normalized
    # ---------------------------------------------------------
    # Swing detection
    # ---------------------------------------------------------

    def _find_swings(
        self,
        candles: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:

        strength = self.swing_strength

        highs = []
        lows = []

        for i in range(
            strength,
            len(candles) - strength,
        ):
            current = candles[i]

            left = candles[i - strength:i]
            right = candles[i + 1:i + strength + 1]

            if all(
                current["high"] >= candle["high"]
                for candle in left + right
            ):
                highs.append(
                    {
                        "index": i,
                        "price": current["high"],
                        "datetime": current["datetime"],
                    }
                )

            if all(
                current["low"] <= candle["low"]
                for candle in left + right
            ):
                lows.append(
                    {
                        "index": i,
                        "price": current["low"],
                        "datetime": current["datetime"],
                    }
                )

        return {
            "highs": highs,
            "lows": lows,
        }

    def _prices_close(self, first, second, tolerance_pct=None):
        tolerance = (
            self.test_tolerance_pct
            if tolerance_pct is None
            else tolerance_pct
        )

        return abs(first - second) <= abs(second) * tolerance




    def _evaluate_bullish_sequence(
        self,
        candles,
        tests,
        highs,
        timeframe,
    ):
        first = tests[0]
        last = tests[-1]

        between_highs = [
            high
            for high in highs
            if first["index"]
            < high["index"]
            < last["index"]
        ]

        if not between_highs:
            return None

        # The highest intermediate structure becomes
        # the candidate bullish BOS level.
        structure = max(
            between_highs,
            key=lambda item: item["price"],
        )

        structure_level = structure["price"]

        # ---------------------------------------------------------
        # PHASE 1: PRE-BOS PROTECTED TESTS
        # ---------------------------------------------------------
        # At least two protected lows form the reversal setup.
        # The latest protected low is the level that must remain
        # valid until the bullish BOS occurs.
        break_data = self._find_bullish_break(
            candles,
            structure_level,
            last["index"] + 1,
        )

        # No BOS yet.
        if break_data is None:
            return self._candidate(
                family="repeated_level",
                direction="bullish",
                timeframe=timeframe,
                tests=tests,
                structure_level=structure_level,
                structure_broken=False,
                break_index=None,
                break_price=None,
                pullback_detected=False,
                pullback_index=None,
                entry_candidate=False,
                state="forming",
                reason=(
                    "Repeated protected lows detected; "
                    "bullish structure has not broken yet."
                ),
                notes=[
                    "Candidate detector is recall-oriented.",
                    "Pre-BOS sequence requires protected lows.",
                ],
            )

        break_index, break_price = break_data

        # ---------------------------------------------------------
        # PHASE 2: POST-BOS RETEST / THIRD TEST
        # ---------------------------------------------------------
        # After BOS, look for a distinct retest of the protected
        # level. This represents the third low in the taught
        # triple-bottom sequence:
        #
        # Low 1 -> Low 2 -> BOS -> Low 3 / retest
        #
        # The retest must not break the immediately preceding
        # protected low.
        retest_index = self._find_bullish_retest(
            candles,
            protected_level=last["price"],
            break_index=break_index + 1,
        )

        # BOS happened but no post-BOS retest yet.
        if retest_index is None:
            return self._candidate(
                family="repeated_level",
                direction="bullish",
                timeframe=timeframe,
                tests=tests,
                structure_level=structure_level,
                structure_broken=True,
                break_index=break_index,
                break_price=break_price,
                pullback_detected=False,
                pullback_index=None,
                entry_candidate=False,
                state="broken_waiting_pullback",
                reason=(
                    "Protected lows produced a bullish break "
                    "of structure; waiting for post-BOS retest."
                ),
                notes=[
                    "BOS uses an intrabar high; candle close is not required.",
                    "Post-BOS retest is treated as the additional protected test.",
                ],
            )

        # ---------------------------------------------------------
        # PHASE 3: RETEST READY
        # ---------------------------------------------------------
        return self._candidate(
            family="repeated_level",
            direction="bullish",
            timeframe=timeframe,
            tests=tests,
            structure_level=structure_level,
            structure_broken=True,
            break_index=break_index,
            break_price=break_price,
            pullback_detected=True,
            pullback_index=retest_index,
            entry_candidate=True,
            state="pullback_ready",
            reason=(
                "Protected lows, bullish BOS, and post-BOS "
                "retest detected."
            ),
            notes=[
                "Sequence represents Low 1 -> Low 2 -> BOS -> Low 3/retest.",
                "BOS uses an intrabar high; candle close is not required.",
                "Final entry still belongs to the 5m/1m entry layers.",
            ],
        )


    # ---------------------------------------------------------
    # Bullish repeated-level family
    # ---------------------------------------------------------

    def _detect_bullish_repeated_tests(
            self,
            candles,
            lows,
            highs,
            timeframe,
        ):

            candidates = []

            for start in range(len(lows) - 1):

                tests = [lows[start]]
                protected_level = lows[start]["price"]

                for candidate in lows[start + 1:]:

                    # IMPORTANT:
                    # A later low breaking below the first protected
                    # low invalidates this protected-level sequence.
                    if candidate["price"] < protected_level:
                        break

                    if self._prices_close(
                        candidate["price"],
                        protected_level,
                    ):
                        tests.append(candidate)

                    if len(tests) >= 2:

                        result = self._evaluate_bullish_sequence(
                            candles,
                            tests,
                            highs,
                            timeframe,
                        )

                        if result is not None:
                            candidates.append(result)

            candidates = self._deduplicate(candidates)
            return self._consolidate_candidates(candidates)

    # ---------------------------------------------------------
    # Bearish repeated-level family
    # ---------------------------------------------------------

    def _detect_bearish_repeated_tests(
            self,
            candles,
            highs,
            lows,
            timeframe,
    ):

            candidates = []

            for start in range(len(highs) - 1):

                tests = [highs[start]]
                protected_level = highs[start]["price"]

                for candidate in highs[start + 1:]:

                    # Mirror rule:
                    # a later high breaking above the protected high
                    # invalidates this protected-level sequence.
                    if candidate["price"] > protected_level:
                        break

                    if self._prices_close(
                        candidate["price"],
                        protected_level,
                    ):
                        tests.append(candidate)

                    if len(tests) >= 2:

                        result = self._evaluate_bearish_sequence(
                            candles,
                            tests,
                            lows,
                            timeframe,
                        )

                        if result is not None:
                            candidates.append(result)

            candidates = self._deduplicate(candidates)
            return self._consolidate_candidates(candidates)



    # ---------------------------------------------------------
    # Bearish sequence
    # ---------------------------------------------------------
    def _evaluate_bearish_sequence(
        self,
        candles,
        tests,
        lows,
        timeframe,
    ):
        first = tests[0]
        last = tests[-1]

        between_lows = [
            low
            for low in lows
            if first["index"]
            < low["index"]
            < last["index"]
        ]

        if not between_lows:
            return None

        # The lowest intermediate structure becomes
        # the candidate bearish BOS level.
        structure = min(
            between_lows,
            key=lambda item: item["price"],
        )

        structure_level = structure["price"]

        # ---------------------------------------------------------
        # PHASE 1: PRE-BOS PROTECTED TESTS
        # ---------------------------------------------------------
        # At least two protected highs form the reversal setup.
        # The latest protected high must remain intact until
        # the bearish BOS occurs.
        break_data = self._find_bearish_break(
            candles,
            structure_level,
            last["index"] + 1,
        )

        # No BOS yet.
        if break_data is None:
            return self._candidate(
                family="repeated_level",
                direction="bearish",
                timeframe=timeframe,
                tests=tests,
                structure_level=structure_level,
                structure_broken=False,
                break_index=None,
                break_price=None,
                pullback_detected=False,
                pullback_index=None,
                entry_candidate=False,
                state="forming",
                reason=(
                    "Repeated protected highs detected; "
                    "bearish structure has not broken yet."
                ),
                notes=[
                    "Candidate detector is recall-oriented.",
                    "Pre-BOS sequence requires protected highs.",
                ],
            )

        break_index, break_price = break_data

        # ---------------------------------------------------------
        # PHASE 2: POST-BOS RETEST / THIRD TEST
        # ---------------------------------------------------------
        # After BOS, look for a distinct retest of the protected
        # level. This represents the third high in the taught
        # triple-top sequence:
        #
        # High 1 -> High 2 -> BOS -> High 3 / retest
        #
        # The retest must not break the immediately preceding
        # protected high.
        retest_index = self._find_bearish_retest(
            candles,
            protected_level=last["price"],
            break_index=break_index + 1,
        )

        # BOS happened but no post-BOS retest yet.
        if retest_index is None:
            return self._candidate(
                family="repeated_level",
                direction="bearish",
                timeframe=timeframe,
                tests=tests,
                structure_level=structure_level,
                structure_broken=True,
                break_index=break_index,
                break_price=break_price,
                pullback_detected=False,
                pullback_index=None,
                entry_candidate=False,
                state="broken_waiting_pullback",
                reason=(
                    "Protected highs produced a bearish break "
                    "of structure; waiting for post-BOS retest."
                ),
                notes=[
                    "BOS uses an intrabar low; candle close is not required.",
                    "Post-BOS retest is treated as the additional protected test.",
                ],
            )

        # ---------------------------------------------------------
        # PHASE 3: RETEST READY
        # ---------------------------------------------------------
        return self._candidate(
            family="repeated_level",
            direction="bearish",
            timeframe=timeframe,
            tests=tests,
            structure_level=structure_level,
            structure_broken=True,
            break_index=break_index,
            break_price=break_price,
            pullback_detected=True,
            pullback_index=retest_index,
            entry_candidate=True,
            state="pullback_ready",
            reason=(
                "Protected highs, bearish BOS, and post-BOS "
                "retest detected."
            ),
            notes=[
                "Sequence represents High 1 -> High 2 -> BOS -> High 3/retest.",
                "BOS uses an intrabar low; candle close is not required.",
                "Final entry still belongs to the 5m/1m entry layers.",
            ],
        )

        # ---------------------------------------------------------
        # BOS
        # ---------------------------------------------------------

    def _find_bullish_break(
        self,
        candles,
        level,
        start_index,
    ):

        for candle in candles[start_index:]:

            if candle["high"] > level:
                return (
                    candle["index"],
                    candle["high"],
                )

        return None

    def _find_bearish_break(
        self,
        candles,
        level,
        start_index,
    ):

        for candle in candles[start_index:]:

            if candle["low"] < level:
                return (
                    candle["index"],
                    candle["low"],
                )

        return None

    def _prices_close(self, first, second, tolerance_pct=None):
        tolerance = (
            self.test_tolerance_pct
            if tolerance_pct is None
            else tolerance_pct
        )

        return abs(first - second) <= abs(second) * tolerance

    def _find_bullish_retest(
        self,
        candles,
        protected_level,
        break_index,
    ):
        """
        Find the first post-BOS bullish retest.

        The retest must interact with the protected pre-BOS
        level within the detector's existing pullback tolerance.

        The retest must not break below the protected level.
        """

        tolerance = abs(protected_level) * self.pullback_tolerance_pct

        lower_bound = protected_level - tolerance
        upper_bound = protected_level + tolerance

        for candle in candles:
            if candle["index"] < break_index:
                continue

            # Price must return to the protected level zone.
            if candle["low"] > upper_bound:
                continue

            # The protected low must remain intact.
            if candle["low"] < protected_level:
                continue

            return candle["index"]

        return None


    def _find_bearish_retest(
        self,
        candles,
        protected_level,
        break_index,
    ):
        """
        Find the first post-BOS bearish retest.

        The retest must interact with the protected pre-BOS
        level within the detector's existing pullback tolerance.

        The retest must not break above the protected level.
        """

        tolerance = abs(protected_level) * self.pullback_tolerance_pct

        lower_bound = protected_level - tolerance
        upper_bound = protected_level + tolerance

        for candle in candles:
            if candle["index"] < break_index:
                continue

            # Price must return to the protected level zone.
            if candle["high"] < lower_bound:
                continue

            # The protected high must remain intact.
            if candle["high"] > protected_level:
                continue

            return candle["index"]

        return None

        # ---------------------------------------------------------
        # Pullback / retest
        # ---------------------------------------------------------

    def _find_bullish_pullback(
        self,
        candles,
        level,
        start_index,
    ):

        tolerance = self.pullback_tolerance_pct

        upper = level * (1 + tolerance)
        lower = level * (1 - tolerance)

        for candle in candles[start_index:]:

            if (
                candle["low"] <= upper
                and candle["high"] >= lower
            ):
                return candle["index"]

        return None

    def _find_bearish_pullback(
        self,
        candles,
        level,
        start_index,
    ):

        tolerance = self.pullback_tolerance_pct

        upper = level * (1 + tolerance)
        lower = level * (1 - tolerance)

        for candle in candles[start_index:]:

            if (
                candle["high"] >= lower
                and candle["low"] <= upper
            ):
                return candle["index"]

        return None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _prices_close(
        self,
        first: float,
        second: float,
        tolerance_pct: float | None = None,
    ) -> bool:

        tolerance = (
            self.test_tolerance_pct
            if tolerance_pct is None
            else tolerance_pct
        )

        return (
            abs(first - second)
            <= abs(second) * tolerance
        )
    def _candidate(
            self,
            family,
            direction,
            timeframe,
            tests,
            structure_level,
            structure_broken,
            break_index,
            break_price,
            pullback_detected,
            pullback_index,
            entry_candidate,
            state,
            reason,
            notes,
        ):

            return ReversalFamilyCandidate(
                family=family,
                direction=direction,
                timeframe=timeframe,
                test_count=len(tests),
                test_points=[
                    dict(test)
                    for test in tests
                ],
                structure_level=structure_level,
                structure_broken=structure_broken,
                break_index=break_index,
                break_price=break_price,
                pullback_detected=pullback_detected,
                pullback_index=pullback_index,
                entry_candidate=entry_candidate,
                valid=True,
                state=state,
                reason=reason,
                detection_notes=notes,
            )

    def _consolidate_candidates(
        self,
        candidates: list[ReversalFamilyCandidate],
    ) -> list[ReversalFamilyCandidate]:
        """
        Consolidate overlapping candidates that represent the same
        evolving reversal formation.

        Example:

            2 tests
            3 tests
            4 tests
            5 tests
            BOS
            pullback

        should be represented as ONE formation rather than many
        independent candidates.

        This does not change the trading rules. It only removes
        duplicate evolutionary snapshots of the same formation.
        """

        if not candidates:
            return []

        # Work chronologically so the formation evolves forward in time.
        ordered = sorted(
            candidates,
            key=lambda candidate: (
                candidate.test_points[0]["index"]
                if candidate.test_points
                else float("inf"),
                candidate.break_index
                if candidate.break_index is not None
                else float("inf"),
            ),
        )

        consolidated: list[ReversalFamilyCandidate] = []

        for candidate in ordered:
            merged = False

            for existing_index, existing in enumerate(consolidated):
                if existing.direction != candidate.direction:
                    continue

                if not existing.test_points or not candidate.test_points:
                    continue

                existing_first = existing.test_points[0]["index"]
                existing_last = existing.test_points[-1]["index"]

                candidate_first = candidate.test_points[0]["index"]
                candidate_last = candidate.test_points[-1]["index"]

                # The formations must overlap in time.
                ranges_overlap = (
                    candidate_first <= existing_last
                    and existing_first <= candidate_last
                )

                if not ranges_overlap:
                    continue

                # Their structural levels must also be close enough
                # to represent the same protected level.
                if not self._prices_close(
                    existing.structure_level,
                    candidate.structure_level,
                    self.test_tolerance_pct,
                ):
                    continue

                # Keep the candidate representing the most developed
                # version of the formation.
                current_score = self._candidate_progress_score(existing)
                new_score = self._candidate_progress_score(candidate)

                if new_score > current_score:
                    consolidated[existing_index] = candidate

                elif new_score == current_score:
                    # Prefer the candidate with more tests.
                    if candidate.test_count > existing.test_count:
                        consolidated[existing_index] = candidate

                merged = True
                break

            if not merged:
                consolidated.append(candidate)

        # Keep output chronological.
        consolidated.sort(
            key=lambda candidate: (
                candidate.test_points[0]["index"]
                if candidate.test_points
                else float("inf")
            )
        )

        return consolidated

    def _candidate_progress_score(
            self,
            candidate: ReversalFamilyCandidate,
        ) -> int:
            """
            Rank an evolutionary formation by how far it has progressed.

            forming
                -> 1

            broken_waiting_pullback
                -> 2

            pullback_ready
                -> 3
            """

            state_scores = {
                "forming": 1,
                "broken_waiting_pullback": 2,
                "pullback_ready": 3,
            }

            return state_scores.get(candidate.state, 0)

    def _deduplicate(self, candidates):

            unique = {}

            for candidate in candidates:

                key = (
                    candidate.direction,
                    candidate.test_points[0]["index"],
                    candidate.test_points[-1]["index"],
                    candidate.structure_level,
                    candidate.break_index,
                )

                unique[key] = candidate

            return list(unique.values())