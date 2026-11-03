from __future__ import annotations

import time
from datetime import datetime
from typing import Callable


class ProactiveMonitorService:
    """
    Continuously runs Tradewisser's proactive scan cycle.

    This service controls scheduling only. It does not perform
    market analysis or make trading decisions.
    """

    def __init__(
        self,
        scan_service,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] | None = None,
    ):
        self._scan_service = scan_service
        self._clock = clock or datetime.now
        self._sleep = sleep or time.sleep
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def run_once(self) -> list[dict]:
        """
        Execute one proactive scan cycle.
        """
        now = self._clock()
        return self._scan_service.run_due_scans(now)

    def run_forever(self, interval_seconds: int = 1) -> None:
        """
        Continuously execute proactive scan cycles.

        The scan service itself determines which instruments
        are actually due.
        """
        if interval_seconds <= 0:
            raise ValueError(
                "Monitor interval must be greater than zero."
            )

        self._running = True

        try:
            while self._running:
                self.run_once()
                self._sleep(interval_seconds)
        finally:
            self._running = False

    def stop(self) -> None:
        """
        Stop the continuous monitoring loop.
        """
        self._running = False