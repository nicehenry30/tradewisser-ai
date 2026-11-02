from app.models.trade_proposal import TradeProposal


class ExecutionAuthorization:
    def __init__(
        self,
        status: str,
        reasons: list[str],
    ):
        self.status = status
        self.reasons = reasons


class ExecutionAuthorizationService:
    @staticmethod
    def authorize(
        trade_proposal: TradeProposal,
        validation_errors: list[str],
        risk_management: dict | None,
    ) -> ExecutionAuthorization:

        if trade_proposal.direction == "WAIT":
            return ExecutionAuthorization(
                status="REJECTED",
                reasons=[
                    "Trade direction is WAIT."
                ],
            )

        if validation_errors:
            return ExecutionAuthorization(
                status="REJECTED",
                reasons=[
                    "Trade proposal contains price validation errors."
                ],
            )

        if risk_management is None:
            return ExecutionAuthorization(
                status="REJECTED",
                reasons=[
                    "Risk management approval is required."
                ],
            )

        required_risk_fields = (
            "risk_percent",
            "risk_amount",
            "position_size",
        )

        if any(
            field not in risk_management
            for field in required_risk_fields
        ):
            return ExecutionAuthorization(
                status="REJECTED",
                reasons=[
                    "Risk management result is incomplete."
                ],
            )

        return ExecutionAuthorization(
            status="AUTHORIZED",
            reasons=[
                "Trade proposal passed all pre-execution checks."
            ],
        )

    
    def test_missing_position_size_rejects_authorization():
        proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        entry=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        confidence=80,
    )

        result = ExecutionAuthorizationService.authorize(
        trade_proposal=proposal,
        validation_errors=[],
        risk_management={
            "symbol": "XAUUSD",
            "risk_percent": 1.0,
            "risk_amount": 100.0,
        },
    )

        assert result.status == "REJECTED"
        assert result.reasons == [
            "Risk management result is incomplete."
    ]


def test_missing_risk_amount_rejects_authorization():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        entry=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        confidence=80,
    )

    result = ExecutionAuthorizationService.authorize(
        trade_proposal=proposal,
        validation_errors=[],
        risk_management={
            "symbol": "XAUUSD",
            "risk_percent": 1.0,
            "position_size": 0.2,
        },
    )

    assert result.status == "REJECTED"
    assert result.reasons == [
        "Risk management result is incomplete."
    ]