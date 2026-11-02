from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIInterpretation:
    """
    Structured interpretation produced by Tradewisser AI.

    The AI interprets deterministic market evidence and the
    OpportunityAssessment. It does not independently create
    trading signals, calculate risk, or execute trades.
    """

    summary: str
    reasoning: list[str] = field(default_factory=list)
    key_evidence: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    next_step: str = "WAIT"
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "reasoning": self.reasoning,
            "key_evidence": self.key_evidence,
            "uncertainty": self.uncertainty,
            "next_step": self.next_step,
            "limitations": self.limitations,
        }