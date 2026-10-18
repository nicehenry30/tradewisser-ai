from pydantic import BaseModel, Field


class TradeRequest(BaseModel):
    """
    Represents the trading context and constraints provided
    by the trader before Tradewisser generates a proposal.
    """

    symbol: str = Field(
        min_length=1,
        description="Trading instrument symbol, for example XAUUSD.",
    )

    account_balance: float = Field(
        gt=0,
        description="Trader's account balance.",
    )

    risk_percent: float = Field(
        gt=0,
        le=100,
        description="Percentage of account balance the trader is willing to risk.",
    )

    entry_price: float | None = Field(
        default=None,
        gt=0,
        description="Trader-provided entry price, if available.",
    )

    stop_loss_price: float | None = Field(
        default=None,
        gt=0,
        description="Trader-provided stop-loss price, if available.",
    )

    take_profit_price: float | None = Field(
        default=None,
        gt=0,
        description="Trader-provided take-profit price, if available.",
    )