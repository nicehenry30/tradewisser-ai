from typing import Literal

from pydantic import BaseModel, Field


class TakeProfitCandidate(BaseModel):
    """
    A deterministic structural take-profit candidate.

    This is a target identified from existing market structure
    or higher-timeframe reference levels. It is not an execution
    instruction.
    """

    price: float = Field(
        gt=0,
        description="Candidate take-profit price.",
    )

    source: str = Field(
        min_length=1,
        description="Source of the target, for example 15m_structure.",
    )

    basis: str = Field(
        min_length=1,
        description="Why this level is considered a target.",
    )

    risk_reward_ratio: float | None = Field(
        default=None,
        ge=0,
        description="Risk/reward ratio from entry to this target.",
    )


class TradeProposal(BaseModel):
    """
    Deterministic trade proposal produced after opportunity,
    15M setup, and 5M confirmation have qualified.

    This represents a proposed trade only.
    It is NOT approved for execution.

    Risk calculation, position sizing, and execution belong
    to downstream layers.
    """

    symbol: str = Field(
        min_length=1,
        description="Trading instrument symbol, for example XAUUSD.",
    )

    direction: Literal["BUY", "SELL", "WAIT"]

    setup_family: str | None = Field(
        default=None,
        description="15M setup family.",
    )

    setup_type: str | None = Field(
        default=None,
        description="15M setup type.",
    )

    entry: float | None = Field(
        default=None,
        gt=0,
        description="Proposed entry price.",
    )

    stop_loss: float | None = Field(
        default=None,
        gt=0,
        description="Proposed structural stop-loss price.",
    )

    take_profit: float | None = Field(
        default=None,
        gt=0,
        description="Primary selected take-profit price.",
    )

    take_profit_candidates: list[TakeProfitCandidate] = Field(
        default_factory=list,
        description="Deterministic structural take-profit candidates.",
    )

    risk_distance: float | None = Field(
        default=None,
        ge=0,
        description="Price distance between entry and stop loss.",
    )

    reward_distance: float | None = Field(
        default=None,
        ge=0,
        description="Price distance between entry and selected take profit.",
    )

    risk_reward_ratio: float | None = Field(
        default=None,
        ge=0,
        description="Risk/reward ratio for the selected target.",
    )

    entry_basis: str | None = Field(
        default=None,
        description="Reason the entry price was selected.",
    )

    stop_basis: str | None = Field(
        default=None,
        description="Structural basis for the stop loss.",
    )

    confidence: float = Field(
        ge=0,
        le=100,
        description="AI confidence score from 0 to 100.",
    )

    market_regime: str | None = Field(
        default=None,
        description="Market regime identified by the analysis.",
    )

    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons supporting the proposed trade.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings or uncertainties identified by the analysis.",
    )