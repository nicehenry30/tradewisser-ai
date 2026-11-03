from datetime import datetime, timedelta

from app.services.proactive_monitor_service import (
    ProactiveMonitorService,
)


class FakeScanService:
    def __init__(self):
        self.calls = []

    def run_due_scans(self, now):
        self.calls.append(now)
        return [{"symbol": "XAUUSD"}]


def test_run_once_executes_scan_cycle():
    scan_service = FakeScanService()

    now = datetime(2026, 11, 3, 10, 0, 0)

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        clock=lambda: now,
        sleep=lambda _: None,
    )

    result = monitor.run_once()

    assert result == [{"symbol": "XAUUSD"}]
    assert scan_service.calls == [now]


def test_monitor_starts_not_running():
    scan_service = FakeScanService()

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        sleep=lambda _: None,
    )

    assert monitor.running is False


def test_run_forever_can_be_stopped():
    scan_service = FakeScanService()

    call_count = 0

    def fake_sleep(_):
        nonlocal call_count
        call_count += 1

        if call_count >= 2:
            monitor.stop()

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        clock=lambda: datetime(2026, 11, 3, 10, 0, 0),
        sleep=fake_sleep,
    )

    monitor.run_forever(interval_seconds=1)

    assert len(scan_service.calls) == 2
    assert monitor.running is False


def test_monitor_rejects_invalid_interval():
    scan_service = FakeScanService()

    monitor = ProactiveMonitorService(
        scan_service=scan_service,
        sleep=lambda _: None,
    )

    try:
        monitor.run_forever(interval_seconds=0)
    except ValueError as exc:
        assert str(exc) == (
            "Monitor interval must be greater than zero."
        )
    else:
        raise AssertionError(
            "Expected ValueError for invalid monitor interval."
        )