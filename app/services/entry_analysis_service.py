from __future__ import annotations

from typing import Any

from app.models.entry_analysis_context import EntryAnalysisContext
from app.services.fifteen_minute_setup_service import FifteenMinuteSetupService


class EntryAnalysisService:
    """
    Orchestrates entry analysis after Tradewisser AI has
    authorized the system to proceed.

    This service does not:
        - generate the market-level opportunity
        - override the OpportunityAssessment
        - calculate risk
        - calculate position size
        - execute trades

    The existing FifteenMinuteSetupService remains responsible
    for 15M structural setup analysis.
    """

    def __init__(
        self,
        fifteen_minute_setup_service: FifteenMinuteSetupService | None = None,
    ):
        self.fifteen_minute_setup_service = (
            fifteen_minute_setup_service
            or FifteenMinuteSetupService()
        )

    def analyze(
        self,
        context: EntryAnalysisContext,
        candles: list[dict[str, Any]],
        higher_timeframe_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run entry analysis only when the controlled context
        authorizes progression.

        A 15M qualified setup is not an entry instruction.
        It only means the 15M structural conditions qualify
        for continued entry analysis.
        """

        if not context.proceed_to_entry_analysis:
            return {
                "status": "WAIT",
                "proceed_to_confirmation": False,
                "reason": (
                    "Entry analysis is blocked because the "
                    "market-level opportunity has not been "
                    "authorized for entry analysis."
                ),
                "setup": None,
            }

        setup = self.fifteen_minute_setup_service.analyze(
            candles=candles,
            higher_timeframe_context=higher_timeframe_context,
        )

        qualified = bool(setup.get("qualified", False))

        return {
            "status": "QUALIFIED" if qualified else "WAIT",
            "proceed_to_confirmation": qualified,
            "reason": (
                "15M structural setup qualified; continue to "
                "lower-timeframe confirmation."
                if qualified
                else "15M structural setup is not qualified."
            ),
            "setup": setup,
        }