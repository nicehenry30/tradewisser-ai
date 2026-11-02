from app.models.trade_proposal import TradeProposal
from app.services.trade_decision_validator import (
    TradeDecisionValidator,
)


def test_wait_proposal_passes_price_validation():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="WAIT",
        confidence=0,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == []


def test_buy_proposal_requires_all_trade_prices():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == [
        "Entry price is required.",
        "Stop-loss price is required.",
        "Take-profit price is required.",
    ]


def test_buy_proposal_rejects_invalid_stop_loss():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        entry=100.0,
        stop_loss=101.0,
        take_profit=105.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == [
        "For a BUY trade, stop-loss must be below entry."
    ]


def test_buy_proposal_rejects_invalid_take_profit():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        entry=100.0,
        stop_loss=95.0,
        take_profit=99.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == [
        "For a BUY trade, take-profit must be above entry."
    ]


def test_valid_buy_proposal_passes():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="BUY",
        entry=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == []


def test_sell_proposal_rejects_invalid_stop_loss():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="SELL",
        entry=100.0,
        stop_loss=99.0,
        take_profit=95.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == [
        "For a SELL trade, stop-loss must be above entry."
    ]


def test_sell_proposal_rejects_invalid_take_profit():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="SELL",
        entry=100.0,
        stop_loss=105.0,
        take_profit=101.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == [
        "For a SELL trade, take-profit must be below entry."
    ]


def test_valid_sell_proposal_passes():
    proposal = TradeProposal(
        symbol="XAUUSD",
        direction="SELL",
        entry=100.0,
        stop_loss=105.0,
        take_profit=90.0,
        confidence=80,
    )

    errors = TradeDecisionValidator.validate_price_structure(
        proposal
    )

    assert errors == []