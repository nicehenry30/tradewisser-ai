from datetime import datetime
from typing import Callable

from app.models.analysis_request import AnalysisRequest
from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.proactive_scanner_service import ProactiveScannerService
from app.services.signal_decision_service import SignalDecisionService
from app.services.signal_identity_service import SignalIdentityService
from app.services.active_signal_registry import ActiveSignalRegistry


class ProactiveScanService:
    """
    Orchestrates proactive market scans.

    The service determines which instruments are due,
    delegates market analysis to TradewisserAnalysisService,
    converts meaningful analysis results into SignalEvents,
    and maintains signal lifecycle state.

    It does not make trading decisions itself and does not
    execute trades.
    """

    def __init__(
        self,
        scanner_service: ProactiveScannerService,
        analysis_service,
        request_factory: Callable[[str], AnalysisRequest],
        signal_decision_service: SignalDecisionService,
        signal_registry: ActiveSignalRegistry | None = None,
        signal_identity_service: SignalIdentityService | None = None,
    ):
        self._scanner_service = scanner_service
        self._analysis_service = analysis_service
        self._request_factory = request_factory
        self._signal_decision_service = signal_decision_service

        self._signal_registry = (
            signal_registry
            or ActiveSignalRegistry()
        )

        self._signal_identity_service = (
            signal_identity_service
            or SignalIdentityService()
        )

    def run_due_scans(
        self,
        now: datetime,
    ) -> list[dict]:
        due_items = self._scanner_service.get_due_items(now)

        results: list[dict] = []

        for item in due_items:
            symbol = item.symbol.strip().upper()

            try:
                request = self._request_factory(symbol)

                analysis_result = self._analysis_service.analyze(
                    request
                )

                signal_event = (
                    self._signal_decision_service.evaluate(
                        symbol=symbol,
                        analysis_result=analysis_result,
                        detected_at=now,
                    )
                )

                signal_id = None
                lifecycle = None

                if signal_event is not None:
                    signal_id = (
                        self._find_or_create_signal(
                            signal_event
                        )
                    )

                    lifecycle = (
                        self._signal_registry.get_lifecycle(
                            signal_id
                        )
                    )

                results.append(
                    {
                        "symbol": symbol,
                        "result": analysis_result,
                        "signal_event": signal_event,
                        "signal_id": signal_id,
                        "lifecycle": lifecycle,
                    }
                )

            except Exception as exc:
                results.append(
                    {
                        "symbol": symbol,
                        "result": {
                            "status": "ERROR",
                            "error": str(exc),
                        },
                        "signal_event": None,
                        "signal_id": None,
                        "lifecycle": None,
                    }
                )

            finally:
                self._scanner_service.mark_scanned(
                    symbol,
                    now,
                )

        return results

    def _find_or_create_signal(
        self,
        signal: SignalEvent,
    ) -> str:
        existing_signal = (
            self._signal_registry.find_active(
                symbol=signal.symbol,
                direction=signal.direction,
            )
        )

        if existing_signal is not None:
            signal_id = (
                self._signal_identity_service.create_id(
                    existing_signal
                )
            )

            return signal_id

        signal_id = (
            self._signal_identity_service.create_new_id(
                signal
            )
        )

        lifecycle = SignalLifecycle(
            signal_id=signal_id,
            status="NEW",
        )

        self._signal_registry.register(
            signal,
            lifecycle,
        )

        if signal.status == "SIGNAL":
            self._signal_registry.update_lifecycle(
                signal_id,
                "ACTIVE",
            )

        return signal_id
