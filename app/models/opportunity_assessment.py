from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OpportunityAssessment:
    """
    Deterministic synthesis of Tradewisser's market-level evidence.

    This model describes whether the combined evidence represents
    a meaningful opportunity worth advancing to entry analysis.

    It does not calculate entries, position size, risk, or execution.
    """

    direction: str
    opportunity: str
    agreement: str
    proceed_to_entry: bool
    supporting_sources: list[str] = field(default_factory=list)
    conflicting_sources: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "opportunity": self.opportunity,
            "agreement": self.agreement,
            "proceed_to_entry": self.proceed_to_entry,
            "supporting_sources": self.supporting_sources,
            "conflicting_sources": self.conflicting_sources,
            "limitations": self.limitations,
        }