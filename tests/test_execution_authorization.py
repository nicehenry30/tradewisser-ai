from app.models.trade_proposal import TradeProposal
from app.services.execution_authorization_service import (
    ExecutionAuthorizationService,
)


def test_valid_risk_approved_proposal_is_authorized():
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
            "position_size": 0.2,
        },
    )

    assert result.status == "AUTHORIZED"
    assert result.reasons == [
        "Trade proposal passed all pre-execution checks."
    ]


def test_wait_proposal_is_rejected():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="WAIT",
        confidence=0,
    )

    result = ExecutionAuthorizationService.authorize(
        trade_proposal=proposal,
        validation_errors=[],
        risk_management=None,
    )

    assert result.status == "REJECTED"
    assert result.reasons == [
        "Trade direction is WAIT."
    ]


def test_price_validation_errors_reject_authorization():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        confidence=80,
    )

    result = ExecutionAuthorizationService.authorize(
        trade_proposal=proposal,
        validation_errors=[
            "Entry price is required.",
            "Stop-loss price is required.",
        ],
        risk_management=None,
    )

    assert result.status == "REJECTED"
    assert result.reasons == [
        "Trade proposal contains price validation errors."
    ]


def test_missing_risk_management_rejects_authorization():
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
        risk_management=None,
    )

    assert result.status == "REJECTED"
    assert result.reasons == [
        "Risk management approval is required."
    ]

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