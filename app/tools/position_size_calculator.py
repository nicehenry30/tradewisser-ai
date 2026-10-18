from app.models.instrument import InstrumentSpecification


class PositionSizeCalculator:

    @staticmethod
    def calculate_position_size(
        risk_amount: float,
        entry_price: float,
        stop_loss_price: float,
        instrument: InstrumentSpecification,
    ) -> float:
        """
        Calculate a position size that respects the instrument's
        trading constraints.

        The calculation uses:

            Stop Distance =
                abs(entry price - stop-loss price)

            Number of Ticks =
                Stop Distance / Tick Size

            Risk Per Volume Unit =
                Number of Ticks × Tick Value

            Raw Position Size =
                Risk Amount / Risk Per Volume Unit

        The raw position size is then rounded DOWN to the
        instrument's allowed volume step.

        Rounding down is intentional because rounding upward
        could increase the trader's intended risk.
        """

        if not isinstance(
            instrument,
            InstrumentSpecification,
        ):
            raise TypeError(
                "instrument must be an InstrumentSpecification."
            )

        if risk_amount <= 0:
            raise ValueError(
                "Risk amount must be greater than zero."
            )

        if entry_price <= 0:
            raise ValueError(
                "Entry price must be greater than zero."
            )

        if stop_loss_price <= 0:
            raise ValueError(
                "Stop-loss price must be greater than zero."
            )

        if entry_price == stop_loss_price:
            raise ValueError(
                "Entry price and stop-loss price cannot be the same."
            )

        stop_distance = abs(
            entry_price - stop_loss_price
        )

        number_of_ticks = (
            stop_distance / instrument.tick_size
        )

        risk_per_volume_unit = (
            number_of_ticks * instrument.tick_value
        )

        if risk_per_volume_unit <= 0:
            raise ValueError(
                "Calculated risk per volume unit must be greater than zero."
            )

        raw_position_size = (
            risk_amount / risk_per_volume_unit
        )

        position_size = (
            int(
                raw_position_size
                / instrument.volume_step
            )
            * instrument.volume_step
        )

        position_size = round(
            position_size,
            8,
        )

        if position_size < instrument.minimum_volume:
            raise ValueError(
                "Calculated position size is below the "
                f"minimum allowed volume of "
                f"{instrument.minimum_volume}."
            )

        if position_size > instrument.maximum_volume:
            position_size = instrument.maximum_volume

        return position_size