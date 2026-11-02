from app.services.ai_interpretation_service import (
    AIInterpretationService,
)
from app.services.entry_analysis_service import (
    EntryAnalysisService,
)
from app.services.evidence_service import EvidenceService
from app.services.execution_authorization_service import (
    ExecutionAuthorizationService,
)
from app.services.five_minute_confirmation_service import (
    FiveMinuteConfirmationService,
)
from app.services.instrument_service import InstrumentService
from app.services.market_data_service import MarketDataService
from app.services.risk_management_service import (
    RiskManagementService,
)
from app.services.tradewisser_analysis_service import (
    TradewisserAnalysisService,
)
from app.services.trade_decision_validator import (
    TradeDecisionValidator,
)
from app.services.trade_proposal_service import (
    TradeProposalService,
)
from app.tools.position_size_calculator import (
    PositionSizeCalculator,
)
from app.tools.risk_calculator import RiskCalculator
from app.tools.risk_policy import RiskPolicy


def create_analysis_service() -> TradewisserAnalysisService:
    """
    Build the production Tradewisser analysis service
    and all of its dependencies.
    """

    evidence_service = EvidenceService()

    ai_interpretation_service = AIInterpretationService()

    entry_analysis_service = EntryAnalysisService()

    five_minute_confirmation_service = (
        FiveMinuteConfirmationService()
    )

    trade_proposal_service = TradeProposalService()

    trade_decision_validator = TradeDecisionValidator()

    market_data_service = MarketDataService()

    risk_policy = RiskPolicy(
        maximum_risk_percent=2.0,
    )

    risk_calculator = RiskCalculator()

    instrument_service = InstrumentService()

    position_size_calculator = PositionSizeCalculator()

    risk_management_service = RiskManagementService(
        risk_policy=risk_policy,
        risk_calculator=risk_calculator,
        instrument_service=instrument_service,
        position_size_calculator=position_size_calculator,
    )

    execution_authorization_service = (
        ExecutionAuthorizationService
    )

    return TradewisserAnalysisService(
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
            execution_authorization_service
        ),
    )