from app.services.tradewisser_analysis_service import (
    TradewisserAnalysisService,
)
from app.models.analysis_request import AnalysisRequest


class StubEvidenceService:
    def __init__(self):
        self.build_calls = []
        self.assess_calls = []
        self.assessment = StubOpportunityAssessment()

    def build_evidence(
        self,
        candles,
        daily_candles,
        four_hour_candles,
        forward_bars=5,
        symbol=None,
    ):
        self.build_calls.append(
            {
                "candles": candles,
                "daily_candles": daily_candles,
                "four_hour_candles": four_hour_candles,
                "forward_bars": forward_bars,
                "symbol": symbol,
            }
        )

        return {
            "sources": ["market_analysis"],
            "higher_timeframe_context": {
                "preferred_direction": "BUY",
            },
            "market_analysis": {
                "trend": "bullish",
            },
        }

    def assess_opportunity(self, evidence):
        self.assess_calls.append(evidence)

        return self.assessment


class StubOpportunityAssessment:
    direction = "LONG"
    opportunity = "HIGH_QUALITY"
    agreement = "HIGH"
    proceed_to_entry = True
    supporting_sources = ["market_analysis"]
    conflicting_sources = []
    limitations = []


class StubAIInterpretationService:
    def __init__(self):
        self.calls = []
        self.next_step = "PROCEED_TO_ENTRY_ANALYSIS"

    def interpret(self, evidence, assessment):
        self.calls.append(
            {
                "evidence": evidence,
                "assessment": assessment,
            }
        )

        interpretation = StubAIInterpretation()
        interpretation.next_step = self.next_step
        return interpretation


class StubAIInterpretation:
    next_step = "PROCEED_TO_ENTRY_ANALYSIS"


class StubEntryAnalysisService:
    def __init__(self):
        self.calls = []
        self.proceed_to_confirmation = True

    def analyze(
        self,
        context,
        candles,
        higher_timeframe_context,
    ):
        self.calls.append(
            {
                "context": context,
                "candles": candles,
                "higher_timeframe_context": (
                    higher_timeframe_context
                ),
            }
        )

        if not self.proceed_to_confirmation:
            return {
                "status": "WAIT",
                "proceed_to_confirmation": False,
                "setup": None,
            }

        return {
            "status": "QUALIFIED",
            "proceed_to_confirmation": True,
            "setup": {
                "timeframe": "15m",
                "setup_type": "REVERSAL_CHOCH",
                "direction": "bullish",
                "qualified": True,
            },
        }


class StubFiveMinuteConfirmationService:
    def __init__(self):
        self.calls = []

    def analyze(
        self,
        candles,
        fifteen_minute_setup,
    ):
        self.calls.append(
            {
                "candles": candles,
                "fifteen_minute_setup": (
                    fifteen_minute_setup
                ),
            }
        )

        return {
            "status": "CONFIRMED",
            "confirmation_state": "CONFIRMED",
            "confirmed": True,
            "direction": "bullish",
        }


class StubTradeProposalService:
    def __init__(self):
        self.calls = []

    def propose(
        self,
        symbol,
        fifteen_minute_setup,
        five_minute_confirmation,
        current_price,
        market_analysis,
        higher_timeframe_context,
    ):
        self.calls.append(
            {
                "symbol": symbol,
                "fifteen_minute_setup": (
                    fifteen_minute_setup
                ),
                "five_minute_confirmation": (
                    five_minute_confirmation
                ),
                "current_price": current_price,
                "market_analysis": market_analysis,
                "higher_timeframe_context": (
                    higher_timeframe_context
                ),
            }
        )

        return StubTradeProposal()


class StubTradeProposal:
    direction = "BUY"
    entry = 100.0
    stop_loss = 98.0
    take_profit = 104.0


class StubTradeDecisionValidator:
    def __init__(self):
        self.calls = []
        self.validation_errors = []

    def validate_price_structure(self, proposal):
        self.calls.append(proposal)
        return self.validation_errors


class StubMarketDataService:
    def __init__(self):
        self.price_calls = []
        self.candle_calls = []

    def get_price(self, symbol):
        self.price_calls.append(symbol)

        return {
            "symbol": symbol,
            "price": 100.0,
        }

    def get_candles(
        self,
        symbol,
        interval="1h",
        outputsize=20,
    ):
        self.candle_calls.append(
            {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
            }
        )

        return {
            "symbol": symbol,
            "interval": interval,
            "values": [],
        }


class StubRiskManagementService:
    def __init__(self):
        self.calls = []

    def calculate(
        self,
        symbol,
        account_balance,
        risk_percent,
        entry_price,
        stop_loss_price,
    ):
        self.calls.append(
            {
                "symbol": symbol,
                "account_balance": account_balance,
                "risk_percent": risk_percent,
                "entry_price": entry_price,
                "stop_loss_price": stop_loss_price,
            }
        )

        return {
            "symbol": symbol,
            "risk_percent": risk_percent,
            "risk_amount": 100.0,
            "position_size": 0.5,
        }


class StubExecutionAuthorizationService:
    def __init__(self):
        self.calls = []
        self.authorization = StubExecutionAuthorization()

    def authorize(
        self,
        trade_proposal,
        validation_errors,
        risk_management,
    ):
        self.calls.append(
            {
                "trade_proposal": trade_proposal,
                "validation_errors": validation_errors,
                "risk_management": risk_management,
            }
        )

        return self.authorization


class StubExecutionAuthorization:
    status = "AUTHORIZED"
    reasons = [
        "Trade proposal passed all pre-execution checks."
    ]


def test_validated_trade_proposal_reaches_execution_authorization():
    execution_authorization_service = (
        StubExecutionAuthorizationService()
    )

    risk_management_service = StubRiskManagementService()

    service = TradewisserAnalysisService(
        evidence_service=StubEvidenceService(),
        ai_interpretation_service=(
            StubAIInterpretationService()
        ),
        entry_analysis_service=StubEntryAnalysisService(),
        five_minute_confirmation_service=(
            StubFiveMinuteConfirmationService()
        ),
        trade_proposal_service=StubTradeProposalService(),
        trade_decision_validator=StubTradeDecisionValidator(),
        market_data_service=StubMarketDataService(),
        risk_management_service=risk_management_service,
        execution_authorization_service=(
            execution_authorization_service
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "AUTHORIZED"

    assert result["execution_authorization"].status == (
        "AUTHORIZED"
    )

    assert result["execution_authorization"].reasons == [
        "Trade proposal passed all pre-execution checks."
    ]

    assert len(execution_authorization_service.calls) == 1

    assert execution_authorization_service.calls[0] == {
        "trade_proposal": result["trade_proposal"],
        "validation_errors": [],
        "risk_management": {
            "symbol": "EUR/USD",
            "risk_percent": 1.0,
            "risk_amount": 100.0,
            "position_size": 0.5,
        },
    }


def test_complete_analysis_pipeline_reaches_trade_proposal():
    evidence_service = StubEvidenceService()
    ai_interpretation_service = (
        StubAIInterpretationService()
    )
    entry_analysis_service = (
        StubEntryAnalysisService()
    )
    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=(
            trade_proposal_service
        ),
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "AUTHORIZED"

    assert result["opportunity_assessment"].opportunity == (
        "HIGH_QUALITY"
    )

    assert result["ai_interpretation"].next_step == (
        "PROCEED_TO_ENTRY_ANALYSIS"
    )

    assert result["entry_analysis"]["status"] == (
        "QUALIFIED"
    )

    assert result["five_minute_confirmation"]["status"] == (
        "CONFIRMED"
    )

    assert result["trade_proposal"].direction == "BUY"

    assert result["validation_errors"] == []

    assert len(evidence_service.build_calls) == 1
    assert len(evidence_service.assess_calls) == 1
    assert len(ai_interpretation_service.calls) == 1
    assert len(entry_analysis_service.calls) == 1
    assert len(five_minute_confirmation_service.calls) == 1
    assert len(trade_proposal_service.calls) == 1
    assert len(trade_decision_validator.calls) == 1


def test_no_opportunity_stops_before_entry_analysis():
    evidence_service = StubEvidenceService()

    evidence_service.assessment.direction = "WAIT"
    evidence_service.assessment.opportunity = (
        "NO_OPPORTUNITY"
    )
    evidence_service.assessment.proceed_to_entry = False

    ai_interpretation_service = (
        StubAIInterpretationService()
    )
    entry_analysis_service = (
        StubEntryAnalysisService()
    )
    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=(
            trade_proposal_service
        ),
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "WAIT"
    assert result["trade_proposal"] is None
    assert entry_analysis_service.calls == []
    assert five_minute_confirmation_service.calls == []
    assert trade_proposal_service.calls == []


def test_ai_wait_stops_before_entry_analysis():
    evidence_service = StubEvidenceService()

    ai_interpretation_service = (
        StubAIInterpretationService()
    )
    ai_interpretation_service.next_step = "WAIT"

    entry_analysis_service = (
        StubEntryAnalysisService()
    )
    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=(
            trade_proposal_service
        ),
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "WAIT"
    assert result["trade_proposal"] is None
    assert entry_analysis_service.calls == []
    assert five_minute_confirmation_service.calls == []
    assert trade_proposal_service.calls == []


def test_15m_not_qualified_stops_before_5m_confirmation():
    evidence_service = StubEvidenceService()

    ai_interpretation_service = (
        StubAIInterpretationService()
    )

    entry_analysis_service = (
        StubEntryAnalysisService()
    )
    entry_analysis_service.proceed_to_confirmation = False

    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "WAIT"
    assert result["entry_analysis"]["status"] == "WAIT"
    assert result["five_minute_confirmation"] is None
    assert result["trade_proposal"] is None

    assert len(entry_analysis_service.calls) == 1
    assert five_minute_confirmation_service.calls == []
    assert trade_proposal_service.calls == []


def test_5m_not_confirmed_stops_before_trade_proposal():
    evidence_service = StubEvidenceService()

    ai_interpretation_service = (
        StubAIInterpretationService()
    )

    entry_analysis_service = (
        StubEntryAnalysisService()
    )

    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )

    # 15M is qualified, but 5M does not confirm it.

    def unconfirmed_analyze(
        candles,
        fifteen_minute_setup,
    ):
        five_minute_confirmation_service.calls.append(
            {
                "candles": candles,
                "fifteen_minute_setup": (
                    fifteen_minute_setup
                ),
            }
        )

        return {
            "status": "WAIT",
            "confirmation_state": "DEVELOPING",
            "confirmed": False,
            "direction": "bullish",
        }

    five_minute_confirmation_service.analyze = (
        unconfirmed_analyze
    )

    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "WAIT"
    assert result["entry_analysis"]["status"] == "QUALIFIED"
    assert (
        result["five_minute_confirmation"]["confirmed"]
        is False
    )
    assert result["trade_proposal"] is None

    assert len(five_minute_confirmation_service.calls) == 1
    assert trade_proposal_service.calls == []
    assert trade_decision_validator.calls == []


def test_invalid_trade_proposal_is_not_validated():
    evidence_service = StubEvidenceService()

    ai_interpretation_service = (
        StubAIInterpretationService()
    )

    entry_analysis_service = (
        StubEntryAnalysisService()
    )

    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )

    trade_proposal_service = StubTradeProposalService()

    trade_decision_validator = (
        StubTradeDecisionValidator()
    )
    trade_decision_validator.validation_errors = [
        "BUY stop loss must be below entry.",
    ]

    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=(
            ai_interpretation_service
        ),
        entry_analysis_service=(
            entry_analysis_service
        ),
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=(
            trade_decision_validator
        ),
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "INVALID_PROPOSAL"
    assert result["trade_proposal"] is not None
    assert result["validation_errors"] == [
        "BUY stop loss must be below entry.",
    ]

    assert len(trade_decision_validator.calls) == 1


def test_no_opportunity_does_not_request_entry_timeframes_or_price():
    evidence_service = StubEvidenceService()

    assessment = StubOpportunityAssessment()
    assessment.direction = "WAIT"
    assessment.opportunity = "NO_OPPORTUNITY"
    assessment.proceed_to_entry = False

    evidence_service.assessment = assessment

    ai_interpretation_service = StubAIInterpretationService()
    entry_analysis_service = StubEntryAnalysisService()
    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = StubTradeDecisionValidator()
    market_data_service = StubMarketDataService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=ai_interpretation_service,
        entry_analysis_service=entry_analysis_service,
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=trade_decision_validator,
        market_data_service=market_data_service,
        risk_management_service=StubRiskManagementService(),
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="XAU/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "WAIT"

    # Opportunity gate must stop the pipeline before entry analysis.
    assert entry_analysis_service.calls == []
    assert five_minute_confirmation_service.calls == []

    # These are only needed downstream.
    assert market_data_service.price_calls == []
    assert not any(
        call["interval"] in {"15min", "5min"}
        for call in market_data_service.candle_calls
    )


def test_invalid_trade_proposal_does_not_reach_risk_management():
    risk_management_service = StubRiskManagementService()

    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = StubTradeDecisionValidator()
    trade_decision_validator.validation_errors = [
        "Invalid price structure."
    ]

    service = TradewisserAnalysisService(
        evidence_service=StubEvidenceService(),
        ai_interpretation_service=StubAIInterpretationService(),
        entry_analysis_service=StubEntryAnalysisService(),
        five_minute_confirmation_service=(
            StubFiveMinuteConfirmationService()
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=trade_decision_validator,
        market_data_service=StubMarketDataService(),
        risk_management_service=risk_management_service,
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="XAU/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "INVALID_PROPOSAL"
    assert result["validation_errors"] == [
        "Invalid price structure."
    ]
    assert risk_management_service.calls == []


def test_validated_trade_proposal_reaches_risk_management():
    """
    A validated trade proposal must be passed to risk management
    with the account-level risk settings from AnalysisRequest.
    """
    evidence_service = StubEvidenceService()
    ai_interpretation_service = StubAIInterpretationService()
    entry_analysis_service = StubEntryAnalysisService()
    five_minute_confirmation_service = (
        StubFiveMinuteConfirmationService()
    )
    trade_proposal_service = StubTradeProposalService()
    trade_decision_validator = StubTradeDecisionValidator()
    market_data_service = StubMarketDataService()
    risk_management_service = StubRiskManagementService()

    service = TradewisserAnalysisService(
        evidence_service=evidence_service,
        ai_interpretation_service=ai_interpretation_service,
        entry_analysis_service=entry_analysis_service,
        five_minute_confirmation_service=(
            five_minute_confirmation_service
        ),
        trade_proposal_service=trade_proposal_service,
        trade_decision_validator=trade_decision_validator,
        market_data_service=market_data_service,
        risk_management_service=risk_management_service,
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="EUR/USD",
            account_balance=10000.0,
            risk_percent=1.0,
        )
    )

    assert result["status"] == "AUTHORIZED"
    assert result["risk_management"] == {
        "symbol": "EUR/USD",
        "risk_percent": 1.0,
        "risk_amount": 100.0,
        "position_size": 0.5,
    }

    assert len(risk_management_service.calls) == 1

    assert risk_management_service.calls[0] == {
        "symbol": "EUR/USD",
        "account_balance": 10000.0,
        "risk_percent": 1.0,
        "entry_price": 100.0,
        "stop_loss_price": 98.0,
    }


def test_risk_management_rejection_returns_controlled_result():
    risk_management_service = StubRiskManagementService()

    def reject_risk(
        symbol,
        account_balance,
        risk_percent,
        entry_price,
        stop_loss_price,
    ):
        raise ValueError(
            "Requested risk exceeds policy."
        )

    risk_management_service.calculate = reject_risk

    service = TradewisserAnalysisService(
        evidence_service=StubEvidenceService(),
        ai_interpretation_service=(
            StubAIInterpretationService()
        ),
        entry_analysis_service=StubEntryAnalysisService(),
        five_minute_confirmation_service=(
            StubFiveMinuteConfirmationService()
        ),
        trade_proposal_service=StubTradeProposalService(),
        trade_decision_validator=StubTradeDecisionValidator(),
        market_data_service=StubMarketDataService(),
        risk_management_service=risk_management_service,
        execution_authorization_service=(
            StubExecutionAuthorizationService()
        ),
    )

    result = service.analyze(
        AnalysisRequest(
            symbol="XAU/USD",
            account_balance=10000.0,
            risk_percent=5.0,
        )
    )

    assert result["status"] == "RISK_REJECTED"
    assert result["trade_proposal"] is not None
    assert result["validation_errors"] == []
    assert result["risk_management"] is None
    assert result["risk_error"] == (
        "Requested risk exceeds policy."
    )