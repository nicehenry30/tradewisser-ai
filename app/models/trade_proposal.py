from typing import Literal

from pydantic import BaseModel, Field


class TradeProposal(BaseModel):
    """
    Trading idea proposed by the AI.

    This represents what the AI thinks may be a valid setup.
    It is NOT yet approved for execution.
    """

    symbol: str = Field(
        min_length=1,
        description="Trading instrument symbol, for example XAUUSD.",
    )

    direction: Literal["BUY", "SELL", "WAIT"]

    entry: float | None = Field(
        default=None,
        description="Proposed entry price.",
    )

    stop_loss: float | None = Field(
        default=None,
        description="Proposed stop-loss price.",
    )

    take_profit: float | None = Field(
        default=None,
        description="Proposed take-profit price.",
    )

    confidence: float = Field(
        ge=0,
        le=100,
        description="AI confidence score from 0 to 100.",
    )

    market_regime: str | None = Field(
        default=None,
        description="Market regime identified by the AI.",
    )

    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons supporting the proposed trade.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings or uncertainties identified by the AI.",
    )