from app.models.signal_event import SignalEvent
from app.models.signal_lifecycle import SignalLifecycle
from app.services.signal_lifecycle_service import SignalLifecycleService


class ActiveSignalRegistry:
    """
    Tracks registered Tradewisser signals and their lifecycle state.

    Lifecycle transition rules are delegated to
    SignalLifecycleService.

    This registry manages signal state only. It does not make
    trading decisions or authorize trade execution.
    """

    def __init__(
        self,
        lifecycle_service: SignalLifecycleService | None = None,
    ):
        self._signals: dict[
            str,
            tuple[SignalEvent, SignalLifecycle],
        ] = {}

        self._lifecycle_service = (
            lifecycle_service
            or SignalLifecycleService()
        )

    def register(
        self,
        signal: SignalEvent,
        lifecycle: SignalLifecycle,
    ) -> None:
        if lifecycle.signal_id in self._signals:
            raise ValueError(
                f"Signal '{lifecycle.signal_id}' is already registered."
            )

        self._signals[lifecycle.signal_id] = (
            signal,
            lifecycle,
        )

    def get(
        self,
        signal_id: str,
    ) -> SignalEvent | None:
        entry = self._signals.get(
            signal_id.strip().upper()
        )

        if entry is None:
            return None

        return entry[0]

    def get_lifecycle(
        self,
        signal_id: str,
    ) -> SignalLifecycle | None:
        entry = self._signals.get(
            signal_id.strip().upper()
        )

        if entry is None:
            return None

        return entry[1]

    def get_active(
        self,
        signal_id: str,
    ) -> SignalEvent | None:
        normalized_signal_id = signal_id.strip().upper()

        entry = self._signals.get(
            normalized_signal_id
        )

        if entry is None:
            return None

        signal, lifecycle = entry

        if lifecycle.status != "ACTIVE":
            return None

        return signal

    def find_active(
        self,
        symbol: str,
        direction: str,
    ) -> SignalEvent | None:
        normalized_symbol = symbol.strip().upper()
        normalized_direction = direction.strip().upper()

        for signal, lifecycle in self._signals.values():
            if lifecycle.status != "ACTIVE":
                continue

            if (
                signal.symbol == normalized_symbol
                and signal.direction == normalized_direction
            ):
                return signal

        return None

    def find_existing(
        self,
        symbol: str,
        direction: str,
    ) -> SignalEvent | None:
        normalized_symbol = symbol.strip().upper()
        normalized_direction = direction.strip().upper()

        for signal, lifecycle in self._signals.values():
            if lifecycle.status == "EXPIRED":
                continue

            if (
                signal.symbol == normalized_symbol
                and signal.direction == normalized_direction
            ):
                return signal

        return None

    def find_existing_id(
        self,
        symbol: str,
        direction: str,
    ) -> str | None:
        normalized_symbol = symbol.strip().upper()
        normalized_direction = direction.strip().upper()

        for signal_id, (signal, lifecycle) in self._signals.items():
            if lifecycle.status == "EXPIRED":
                continue

            if (
                signal.symbol == normalized_symbol
                and signal.direction == normalized_direction
            ):
                return signal_id

        return None

    def update_lifecycle(
        self,
        signal_id: str,
        new_status: str,
    ) -> SignalLifecycle:
        normalized_signal_id = signal_id.strip().upper()

        entry = self._signals.get(
            normalized_signal_id
        )

        if entry is None:
            raise ValueError(
                f"Signal '{normalized_signal_id}' is not registered."
            )

        signal, current_lifecycle = entry

        updated_lifecycle = (
            self._lifecycle_service.transition(
                current_lifecycle,
                new_status,
            )
        )

        self._signals[normalized_signal_id] = (
            signal,
            updated_lifecycle,
        )

        return updated_lifecycle

    def store_lifecycle(
        self,
        signal_id: str,
        lifecycle: SignalLifecycle,
    ) -> None:
        normalized_signal_id = signal_id.strip().upper()

        entry = self._signals.get(
            normalized_signal_id
        )

        if entry is None:
            raise ValueError(
                f"Signal '{normalized_signal_id}' is not registered."
            )

        signal, _ = entry

        if lifecycle.signal_id != normalized_signal_id:
            raise ValueError(
                "Lifecycle signal ID does not match "
                "the registered signal ID."
            )

        self._signals[normalized_signal_id] = (
            signal,
            lifecycle,
        )

    def update_signal(
        self,
        signal_id: str,
        signal: SignalEvent,
    ) -> None:
        normalized_signal_id = signal_id.strip().upper()

        entry = self._signals.get(normalized_signal_id)

        if entry is None:
            raise ValueError(
                f"Signal '{normalized_signal_id}' is not registered."
            )

        _, lifecycle = entry

        if lifecycle.status == "EXPIRED":
            raise ValueError(
                f"Cannot update expired signal "
                f"'{normalized_signal_id}'."
            )

        self._signals[normalized_signal_id] = (
            signal,
            lifecycle,
        )

    def remove(
        self,
        signal_id: str,
    ) -> None:
        self._signals.pop(
            signal_id.strip().upper(),
            None,
        )
