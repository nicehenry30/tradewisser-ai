from typing import Any

from app.services.structure_engine import StructureEngine


class FifteenMinuteSetupService:
    """
    Interprets 15M market structure in the context of the
    already-calculated higher-timeframe direction.

    Responsibilities:
        - Analyze 15M structure using StructureEngine.
        - Compare 15M structure with HTF directional permission.
        - Identify the latest relevant CHOCH/BOS.
        - Classify the setup as primary or secondary.
        - Determine whether the 15M setup is qualified.

    Setup priority:
        CHOCH -> primary
        BOS   -> secondary

    This service does NOT:
        - calculate Daily structure
        - calculate 4H structure
        - calculate risk
        - calculate position size
        - generate an entry price
        - perform 5M confirmation
        - execute trades
    """

    def __init__(self, structure_engine: StructureEngine | None = None):
        self.structure_engine = structure_engine or StructureEngine()

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

        current_direction = structure["current_direction"]

        latest_choch = self._latest_event(
            structure["events"],
            "CHOCH",
        )

        latest_bos = self._latest_event(
            structure["events"],
            "BOS",
        )

        latest_relevant_event = self._latest_relevant_event(
            latest_choch=latest_choch,
            latest_bos=latest_bos,
            htf_direction=htf_direction,
        )

        setup_type = None
        setup_priority = None
        qualified = False
        alignment = "not_aligned"

        if htf_direction in {"BUY", "SELL"}:
            expected_direction = (
                "bullish"
                if htf_direction == "BUY"
                else "bearish"
            )

            if current_direction == expected_direction:
                alignment = "aligned"

            # CHOCH is the primary transition setup.
            # It can qualify before current_direction flips,
            # because CHOCH itself represents the structural transition.
            if (
                latest_choch is not None
                and latest_choch["direction"] == expected_direction
            ):
                alignment = "aligned"
                setup_type = "CHOCH"
                setup_priority = "primary"
                qualified = True

            # BOS is a secondary setup and requires the current
            # structure to already agree with the HTF direction.
            elif (
                latest_bos is not None
                and latest_bos["direction"] == expected_direction
                and current_direction == expected_direction
            ):
                alignment = "aligned"
                setup_type = "BOS"
                setup_priority = "secondary"
                qualified = True

        return {
            "timeframe": "15m",
            "htf_direction": htf_direction,
            "structure_direction": current_direction,
            "structure_state": structure["current_state"],
            "alignment": alignment,
            "latest_choch": latest_choch,
            "latest_bos": latest_bos,
            "latest_relevant_event": latest_relevant_event,
            "setup_type": setup_type,
            "setup_priority": setup_priority,
            "qualified": qualified,
            "structure": structure,
        }

    @staticmethod
    def _latest_event(
        events: list[dict[str, Any]],
        event_type: str,
    ) -> dict[str, Any] | None:
        matching = [
            event
            for event in events
            if event.get("event_type") == event_type
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda event: event["index"],
        )

    @staticmethod
    def _latest_relevant_event(
        latest_choch: dict[str, Any] | None,
        latest_bos: dict[str, Any] | None,
        htf_direction: str,
    ) -> dict[str, Any] | None:
        if htf_direction == "BUY":
            expected_direction = "bullish"
        elif htf_direction == "SELL":
            expected_direction = "bearish"
        else:
            return None

        candidates = [
            event
            for event in (latest_choch, latest_bos)
            if (
                event is not None
                and event.get("direction") == expected_direction
            )
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda event: event["index"],
        )