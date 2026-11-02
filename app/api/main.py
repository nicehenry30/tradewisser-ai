from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.api.composition import create_analysis_service
from app.api.serializers import serialize_analysis_result
from app.models.analysis_request import AnalysisRequest


app = FastAPI(
    title="Tradewisser AI API",
    version="1.0.0",
    description="Internal API for the Tradewisser AI market-analysis engine.",
)


class AnalyzeRequest(BaseModel):
    """
    HTTP request model received by the FastAPI layer.
    """

    symbol: str = Field(
        ...,
        min_length=1,
        description="Trading symbol, for example XAU/USD.",
    )

    account_balance: float = Field(
        ...,
        gt=0,
        description="Trading account balance.",
    )

    risk_percent: float = Field(
        ...,
        gt=0,
        description="Percentage of account balance to risk.",
    )


analysis_service = create_analysis_service()


@app.get("/health")
def health():
    """
    Simple health-check endpoint.
    """

    return {
        "status": "ok",
        "service": "tradewisser-ai",
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Run the existing Tradewisser analysis pipeline.
    """

    analysis_request = AnalysisRequest(
        symbol=request.symbol,
        account_balance=request.account_balance,
        risk_percent=request.risk_percent,
    )

    result = analysis_service.analyze(analysis_request)

    return serialize_analysis_result(result)
