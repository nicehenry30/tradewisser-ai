from typing import Literal

from pydantic import BaseModel, Field


class TradeDecision(BaseModel):
    """
    Structured representation of a Tradewisser trading decision.

    The LLM may propose these values, but the application
    must validate them before they can be considered executable.
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

    risk_amount: float | None = Field(
        default=None,
        ge=0,
        description="Maximum monetary amount the trader is willing to risk.",
    )

    position_size: float | None = Field(
        default=None,
        ge=0,
        description="Calculated trading position size.",
    )

    confidence: float = Field(
        ge=0,
        le=100,
        description="AI confidence score from 0 to 100.",
    )

    market_regime: str | None = Field(
        default=None,
        description="Current market regime.",
    )

    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons supporting the decision.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings or uncertainties associated with the decision.",
    )

    allowed_to_trade: bool = False