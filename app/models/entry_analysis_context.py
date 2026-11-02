from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EntryAnalysisContext:
    """
    Controlled handoff from Tradewisser AI to the entry-analysis layer.

    This model does not contain an entry, stop loss, take profit,
    position size, risk calculation, or execution instruction.

    It only communicates whether the deterministic opportunity
    assessment allows the system to proceed to entry analysis and
    the market context that entry analysis is allowed to use.
    """

    direction: str
    opportunity: str
    proceed_to_entry_analysis: bool
    ai_next_step: str
    supporting_sources: list[str] = field(default_factory=list)
    conflicting_sources: list[str] = field(default_factory=list)
    key_evidence: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "direction": self.direction,
            "opportunity": self.opportunity,
            "proceed_to_entry_analysis": self.proceed_to_entry_analysis,
            "ai_next_step": self.ai_next_step,
            "supporting_sources": self.supporting_sources,
            "conflicting_sources": self.conflicting_sources,
            "key_evidence": self.key_evidence,
            "uncertainty": self.uncertainty,
            "limitations": self.limitations,
        }