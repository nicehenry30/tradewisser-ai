from app.models.analysis_request import AnalysisRequest
from app.models.entry_analysis_context import EntryAnalysisContext


class TradewisserAnalysisService:
    """
    Top-level deterministic orchestration service for Tradewisser AI.

    Connects the existing analytical and trade-analysis services
    without replacing their individual responsibilities.
    """

    def __init__(
        self,
        evidence_service,
        ai_interpretation_service,
        entry_analysis_service,
        five_minute_confirmation_service,
        trade_proposal_service,
        trade_decision_validator,
        market_data_service,
        risk_management_service,
        execution_authorization_service,
    ):
        self.evidence_service = evidence_service
        self.ai_interpretation_service = (
            ai_interpretation_service
        )
        self.entry_analysis_service = (
            entry_analysis_service
        )
        self.five_minute_confirmation_service = (
            five_minute_confirmation_service
        )
        self.trade_proposal_service = (
            trade_proposal_service
        )
        self.trade_decision_validator = (
            trade_decision_validator
        )
        self.market_data_service = market_data_service
        self.risk_management_service = (
            risk_management_service
        )
        self.execution_authorization_service = (
            execution_authorization_service
        )

    def analyze(self, request: AnalysisRequest):
        """
        Run the complete deterministic analysis pipeline.
        """
        symbol = request.symbol

        candles = self._get_candles(
            symbol=symbol,
            interval="1h",
            outputsize=100,
        )

        daily_candles = self._get_candles(
            symbol=symbol,
            interval="1day",
            outputsize=100,
        )

        four_hour_candles = self._get_candles(
            symbol=symbol,
            interval="4h",
            outputsize=100,
        )

        evidence = self.evidence_service.build_evidence(
            candles=candles,
            daily_candles=daily_candles,
            four_hour_candles=four_hour_candles,
            forward_bars=5,
            symbol=symbol,
        )

        assessment = (
            self.evidence_service.assess_opportunity(
                evidence
            )
        )

        ai_interpretation = (
            self.ai_interpretation_service.interpret(
                evidence=evidence,
                assessment=assessment,
            )
        )

        # NO_OPPORTUNITY must stop here.
        #
        # POTENTIAL is different: it means the higher-timeframe
        # evidence is conflicting but still deserves lower-timeframe
        # investigation. It is NOT trade authorization.
        #
        # VALID / HIGH_QUALITY can proceed normally to entry analysis.
        can_investigate_lower_timeframe = (
            assessment.opportunity == "POTENTIAL"
            and ai_interpretation.next_step
            == "INVESTIGATE_LOWER_TIMEFRAME"
        ) or (
            assessment.opportunity in {
                "VALID",
                "HIGH_QUALITY",
            }
            and ai_interpretation.next_step
            == "PROCEED_TO_ENTRY_ANALYSIS"
        )

        if not can_investigate_lower_timeframe:
            return {
                "status": "WAIT",
                "evidence": evidence,
                "opportunity_assessment": assessment,
                "ai_interpretation": ai_interpretation,
                "entry_analysis_context": None,
                "entry_analysis": None,
                "five_minute_confirmation": None,
                "trade_proposal": None,
                "validation_errors": [],
            }

        fifteen_minute_candles = self._get_candles(
            symbol=symbol,
            interval="15min",
            outputsize=100,
        )

        entry_analysis_context = (
            EntryAnalysisContext(
                direction=assessment.direction,
                opportunity=assessment.opportunity,
                proceed_to_entry_analysis=True,
                ai_next_step=ai_interpretation.next_step,
                supporting_sources=(
                    assessment.supporting_sources
                ),
                conflicting_sources=(
                    assessment.conflicting_sources
                ),
                key_evidence={},
                uncertainty=[],
                limitations=assessment.limitations,
            )
        )

        # EvidenceService already calculated the raw
        # higher-timeframe context during build_evidence().
        # Reuse it instead of recalculating Daily/4H analysis.
        higher_timeframe_context = (
            self._get_higher_timeframe_context()
        )

        entry_analysis = (
            self.entry_analysis_service.analyze(
                context=entry_analysis_context,
                candles=fifteen_minute_candles,
                higher_timeframe_context=(
                    higher_timeframe_context
                ),
            )
        )

        if not entry_analysis.get(
            "proceed_to_confirmation",
            False,
        ):
            return {
                "status": "WAIT",
                "evidence": evidence,
                "opportunity_assessment": assessment,
                "ai_interpretation": ai_interpretation,
                "entry_analysis_context": (
                    entry_analysis_context
                ),
                "entry_analysis": entry_analysis,
                "five_minute_confirmation": None,
                "trade_proposal": None,
                "validation_errors": [],
            }

        five_minute_candles = self._get_candles(
            symbol=symbol,
            interval="5min",
            outputsize=100,
        )

        five_minute_confirmation = (
            self.five_minute_confirmation_service.analyze(
                candles=five_minute_candles,
                fifteen_minute_setup=(
                    entry_analysis["setup"]
                ),
            )
        )

        if not five_minute_confirmation.get(
            "confirmed",
            False,
        ):
            return {
                "status": "WAIT",
                "evidence": evidence,
                "opportunity_assessment": assessment,
                "ai_interpretation": ai_interpretation,
                "entry_analysis_context": (
                    entry_analysis_context
                ),
                "entry_analysis": entry_analysis,
                "five_minute_confirmation": (
                    five_minute_confirmation
                ),
                "trade_proposal": None,
                "validation_errors": [],
            }

        price_data = self.market_data_service.get_price(
            symbol
        )
        current_price = price_data["price"]

        market_analysis = self._get_market_analysis()

        trade_proposal = (
            self.trade_proposal_service.propose(
                symbol=symbol,
                fifteen_minute_setup=(
                    entry_analysis["setup"]
                ),
                five_minute_confirmation=(
                    five_minute_confirmation
                ),
                current_price=current_price,
                market_analysis=market_analysis,
                higher_timeframe_context=(
                    higher_timeframe_context
                ),
            )
        )

        validation_errors = (
            self.trade_decision_validator.validate_price_structure(
                trade_proposal
            )
        )

        if validation_errors:
            status = "INVALID_PROPOSAL"
            risk_management = None
            risk_error = None
            execution_authorization = None

        else:
            try:
                risk_management = (
                    self.risk_management_service.calculate(
                        symbol=symbol,
                        account_balance=request.account_balance,
                        risk_percent=request.risk_percent,
                        entry_price=trade_proposal.entry,
                        stop_loss_price=trade_proposal.stop_loss,
                    )
                )

                risk_error = None

                execution_authorization = (
                    self.execution_authorization_service.authorize(
                        trade_proposal=trade_proposal,
                        validation_errors=validation_errors,
                        risk_management=risk_management,
                    )
                )

                if (
                    execution_authorization.status
                    == "AUTHORIZED"
                ):
                    status = "AUTHORIZED"
                else:
                    status = "AUTHORIZATION_REJECTED"

            except ValueError as exc:
                risk_management = None
                risk_error = str(exc)
                execution_authorization = None
                status = "RISK_REJECTED"

        return {
            "status": status,
            "evidence": evidence,
            "opportunity_assessment": assessment,
            "ai_interpretation": ai_interpretation,
            "entry_analysis_context": (
                entry_analysis_context
            ),
            "entry_analysis": entry_analysis,
            "five_minute_confirmation": (
                five_minute_confirmation
            ),
            "trade_proposal": trade_proposal,
            "validation_errors": validation_errors,
            "risk_management": risk_management,
            "risk_error": risk_error,
            "execution_authorization": (
                execution_authorization
            ),
        }

    def _get_candles(
        self,
        symbol,
        interval,
        outputsize,
    ):
        response = self.market_data_service.get_candles(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
        )

        return response.get("candles", [])

    def _get_higher_timeframe_context(self):
        """
        Reuse the raw higher-timeframe context produced by
        EvidenceService during the current analysis run.

        Test doubles that do not expose the getter safely fall
        back to an empty context.
        """
        getter = getattr(
            self.evidence_service,
            "get_last_higher_timeframe_context",
            None,
        )

        if getter is None:
            return {}

        return getter() or {}

    def _get_market_analysis(self):
        """
        Reuse the raw market analysis generated by EvidenceService
        during the current analysis run.

        Test doubles that do not expose the getter safely fall
        back to an empty context.
        """
        getter = getattr(
            self.evidence_service,
            "get_last_market_analysis",
            None,
        )

        if getter is None:
            return {}

        return getter() or {}