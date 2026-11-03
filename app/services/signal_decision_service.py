from datetime import datetime

from app.models.signal_event import SignalEvent


class SignalDecisionService:
    """
    Converts a completed Tradewisser analysis result into
    a user-facing SignalEvent when the result is meaningful.

    This service does not execute trades and does not replace
    risk management or execution authorization.
    """

    def evaluate(
        self,
        symbol: str,
        analysis_result: dict,
        detected_at: datetime,
    ) -> SignalEvent | None:
        status = analysis_result.get("status")

        opportunity_assessment = analysis_result.get(
            "opportunity_assessment"
        ) or {}

        ai_interpretation = analysis_result.get(
            "ai_interpretation"
        ) or {}

        direction = opportunity_assessment.get("direction", "NEUTRAL")
        opportunity = opportunity_assessment.get("opportunity")

        confidence = float(
            ai_interpretation.get("confidence", 0.0)
        )

        reason = ai_interpretation.get(
            "summary",
            "Tradewisser detected a market condition worth monitoring.",
        )

        # A fully authorized analysis becomes a user-facing signal.
        if status == "AUTHORIZED":
            return SignalEvent(
                symbol=symbol,
                direction=direction,
                status="SIGNAL",
                confidence=confidence,
                reason=reason,
                detected_at=detected_at,
            )

        # A potential opportunity is worth notifying the user about,
        # but it is not a trade authorization.
        if opportunity == "POTENTIAL":
            return SignalEvent(
                symbol=symbol,
                direction=direction,
                status="DEVELOPING",
                confidence=confidence,
                reason=reason,
                detected_at=detected_at,
            )

        # WAIT, RISK_REJECTED, and other non-actionable states
        # should not generate proactive signals.
        return None
