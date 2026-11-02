from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceObservation:
    """
    A single measurable observation produced by an analytical source.
    """

    name: str
    value: Any
    unit: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
        }


@dataclass(frozen=True)
class EvidenceSource:
    """
    Normalized evidence produced by one analytical system.

    This represents evidence, not a trading decision.
    """

    source: str
    observations: list[EvidenceObservation] = field(
        default_factory=list
    )
    direction: str = "neutral"
    confidence: float | None = None
    sample_size: int | None = None
    strength: str | None = None
    limitations: list[str] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "direction": self.direction,
            "observations": [
                observation.to_dict()
                for observation in self.observations
            ],
            "confidence": self.confidence,
            "evidence": {
                "sample_size": self.sample_size,
                "strength": self.strength,
            },
            "limitations": self.limitations,
        }