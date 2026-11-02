from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceQuality:
    """
    Describes the quality of an evidence source without making
    a trading decision.

    This model evaluates evidence quality, not trade direction.
    """

    quality: str
    reasons: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "quality": self.quality,
            "reasons": self.reasons,
        }