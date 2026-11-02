from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisRequest:
    symbol: str
    account_balance: float
    risk_percent: float