from dataclasses import dataclass


@dataclass
class MarketConfirmationFacts:
    direction_confirmed: bool
    structure_confirmed: bool
    latest_event_type: str | None
    latest_event_direction: str | None
    opposing_structure: bool

    def to_dict(self):
        return {
            "direction_confirmed": self.direction_confirmed,
            "structure_confirmed": self.structure_confirmed,
            "latest_event_type": self.latest_event_type,
            "latest_event_direction": self.latest_event_direction,
            "opposing_structure": self.opposing_structure,
        }


class MarketConfirmationAdapter:
    """
    Converts MarketAnalysisService output into confirmation facts.

    This layer does NOT create new market-structure rules.
    It only interprets the existing analysis output.
    """

    def build_facts(self, analysis: dict, direction: str) -> MarketConfirmationFacts:
        if direction not in {"bullish", "bearish"}:
            raise ValueError("direction must be 'bullish' or 'bearish'")

        trend = analysis.get("trend")
        events = analysis.get("structure_events", [])

        latest_event = events[-1] if events else None

        latest_event_type = (
            latest_event.get("type")
            if latest_event
            else None
        )

        latest_event_direction = (
            latest_event.get("direction")
            if latest_event
            else None
        )

        direction_confirmed = trend == direction

        structure_confirmed = (
            latest_event_direction == direction
            and latest_event_type in {"BOS", "CHOCH"}
        )

        opposing_structure = (
            latest_event_direction is not None
            and latest_event_direction != direction
        )

        return MarketConfirmationFacts(
            direction_confirmed=direction_confirmed,
            structure_confirmed=structure_confirmed,
            latest_event_type=latest_event_type,
            latest_event_direction=latest_event_direction,
            opposing_structure=opposing_structure,
        )