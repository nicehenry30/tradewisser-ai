from typing import Any

from app.services.structure_engine import StructureEngine
from app.strategy.reversal_family import ReversalFamilyDetector


class FifteenMinuteSetupService:
    """
    Interprets 15M market structure in the context of the
    already-calculated higher-timeframe direction.

    The service identifies a generic 15M setup contract that can
    later support multiple setup families.

    Current setup families:

        REVERSAL
            - REVERSAL_CHOCH
            - REVERSAL_CHOCH_BOS

        CONTINUATION
            - TREND_CONTINUATION_BOS
            - TREND_CONTINUATION_CHOCH_BOS

    This service does NOT:

        - calculate Daily structure
        - calculate 4H structure
        - calculate risk
        - calculate position size
        - generate an entry price
        - perform 5M confirmation
        - execute trades

    The 15M result only determines whether a setup is ready
    to be passed to the 5M confirmation layer.
    """

    REVERSAL = "REVERSAL"
    CONTINUATION = "CONTINUATION"

    REVERSAL_CHOCH = "REVERSAL_CHOCH"
    REVERSAL_CHOCH_BOS = "REVERSAL_CHOCH_BOS"

    TREND_CONTINUATION_BOS = "TREND_CONTINUATION_BOS"
    TREND_CONTINUATION_CHOCH_BOS = (
        "TREND_CONTINUATION_CHOCH_BOS"
    )

    READY_FOR_5M_CONFIRMATION = "READY_FOR_5M_CONFIRMATION"
    WAIT = "WAIT"

    def __init__(
        self,
        structure_engine: StructureEngine | None = None,
        reversal_family_detector: ReversalFamilyDetector | None = None,
    ):
        self.structure_engine = (
            structure_engine or StructureEngine()
        )

        self.reversal_family_detector = (
            reversal_family_detector
            or ReversalFamilyDetector()
        )

    def analyze(
        self,
        candles: list[dict[str, Any]],
        higher_timeframe_context: dict[str, Any],
    ) -> dict[str, Any]:

        htf_direction = higher_timeframe_context.get(
            "preferred_direction",
            "WAIT",
        )

        structure = self.structure_engine.analyze(
            candles=candles,
            timeframe="15m",
        )

        # ----------------------------------------------------------
        # Reversal behavioural family
        #
        # This is diagnostic evidence for now.
        # It does not replace the existing CHOCH/BOS qualification
        # logic below.
        # ----------------------------------------------------------

        reversal_family = {
            "bullish": self.reversal_family_detector.detect(
                candles=candles,
                direction="bullish",
                timeframe="15m",
            ),
            "bearish": self.reversal_family_detector.detect(
                candles=candles,
                direction="bearish",
                timeframe="15m",
            ),
        }

        current_direction = structure.get(
            "current_direction",
            "neutral",
        )

        initial_direction = structure.get(
            "initial_direction",
            current_direction,
        )

        events = sorted(
            structure.get("events", []),
            key=lambda event: event.get("index", -1),
        )

        latest_choch = self._latest_event(
            events,
            "CHOCH",
        )

        latest_bos = self._latest_event(
            events,
            "BOS",
        )

        latest_relevant_event = None

        setup_family = None
        setup_type = None
        setup_priority = None

        structure_pattern: list[str] = []
        trigger = None

        direction = "neutral"
        qualified = False

        alignment = "not_aligned"

        setup_stage = self.WAIT
        confirmation_type = None
        confirmed = False

        if htf_direction in {"BUY", "SELL"}:

            expected_direction = (
                "bullish"
                if htf_direction == "BUY"
                else "bearish"
            )

            if current_direction == expected_direction:
                alignment = "aligned"

            relevant_events = [
                event
                for event in events
                if event.get("direction")
                == expected_direction
            ]

            relevant_choch = self._latest_event(
                relevant_events,
                "CHOCH",
            )

            relevant_bos = self._latest_event(
                relevant_events,
                "BOS",
            )

            latest_relevant_event = (
                relevant_events[-1]
                if relevant_events
                else None
            )

            # ------------------------------------------------------
            # CHOCH-based setup
            # ------------------------------------------------------

            if relevant_choch is not None:

                choch_index = relevant_choch.get(
                    "index",
                    -1,
                )

                bos_after_choch = None

                if relevant_bos is not None:
                    bos_index = relevant_bos.get(
                        "index",
                        -1,
                    )

                    if bos_index > choch_index:
                        bos_after_choch = relevant_bos

                # --------------------------------------------------
                # CHOCH + BOS
                # --------------------------------------------------

                if bos_after_choch is not None:

                    structure_pattern = [
                        "CHOCH",
                        "BOS",
                    ]

                    trigger = "BOS"
                    direction = expected_direction

                    if initial_direction != expected_direction:

                        setup_family = self.REVERSAL

                        setup_type = (
                            self.REVERSAL_CHOCH_BOS
                        )

                    else:

                        setup_family = self.CONTINUATION

                        setup_type = (
                            self.TREND_CONTINUATION_CHOCH_BOS
                        )

                    setup_priority = "primary"
                    qualified = True

                # --------------------------------------------------
                # CHOCH only
                # --------------------------------------------------

                else:

                    # A CHOCH against the initial direction is
                    # sufficient for the current reversal
                    # strategy.
                    if (
                        initial_direction
                        != expected_direction
                    ):

                        setup_family = self.REVERSAL

                        setup_type = (
                            self.REVERSAL_CHOCH
                        )

                        structure_pattern = [
                            "CHOCH",
                        ]

                        trigger = "CHOCH"
                        direction = expected_direction

                        setup_priority = "primary"
                        qualified = True

                    else:

                        # CHOCH alone in an already aligned
                        # trend is not enough to define a
                        # continuation setup yet.
                        #
                        # We deliberately leave it unqualified
                        # until a continuation strategy is
                        # explicitly defined.

                        setup_family = None
                        setup_type = None
                        structure_pattern = []
                        trigger = None
                        direction = expected_direction

                        setup_priority = None
                        qualified = False

            # ------------------------------------------------------
            # BOS-only continuation
            # ------------------------------------------------------

            elif (
                relevant_bos is not None
                and current_direction
                == expected_direction
            ):

                setup_family = self.CONTINUATION

                setup_type = (
                    self.TREND_CONTINUATION_BOS
                )

                structure_pattern = [
                    "BOS",
                ]

                trigger = "BOS"
                direction = expected_direction

                setup_priority = "secondary"
                qualified = True

        # ----------------------------------------------------------
        # Setup stage
        # ----------------------------------------------------------

        if qualified:

            setup_stage = (
                self.READY_FOR_5M_CONFIRMATION
            )

            confirmation_type = "5M_CONFIRMATION"

        return {
            "timeframe": "15m",

            "htf_direction": htf_direction,

            "structure_direction": current_direction,

            "structure_state": structure.get(
                "current_state"
            ),

            "alignment": alignment,

            "latest_choch": latest_choch,

            "latest_bos": latest_bos,

            "latest_relevant_event": (
                latest_relevant_event
            ),

            # Reversal behavioural family.
            #
            # This exposes repeated-level reversal evidence such
            # as:
            #
            # repeated tests
            # -> structure break
            # -> pullback/retest
            # -> entry candidate
            #
            # It is diagnostic at this stage and does not override
            # the existing setup qualification logic.
            "reversal_family": reversal_family,

            # Generic setup contract
            "setup_family": setup_family,
            "setup_type": setup_type,
            "structure_pattern": structure_pattern,
            "trigger": trigger,
            "direction": direction,
            "qualified": qualified,

            # Setup lifecycle
            "setup_priority": setup_priority,
            "setup_stage": setup_stage,

            # Future 5M confirmation contract
            "confirmation_type": confirmation_type,
            "confirmed": confirmed,

            # Raw structure remains available for
            # downstream analysis/debugging.
            "structure": structure,
        }

    @staticmethod
    def _latest_event(
        events: list[dict[str, Any]],
        event_type: str,
    ) -> dict[str, Any] | None:

        matching_events = [
            event
            for event in events
            if event.get("event_type")
            == event_type
        ]

        if not matching_events:
            return None

        return max(
            matching_events,
            key=lambda event: event.get(
                "index",
                -1,
            ),
        )