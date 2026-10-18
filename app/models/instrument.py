from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentSpecification:
    """
    Describes the trading specifications required
    to calculate monetary exposure for an instrument.

    The values should ultimately come from a broker,
    exchange, or trusted market-data source.
    """

    symbol: str
    contract_size: float
    tick_size: float
    tick_value: float
    volume_step: float
    minimum_volume: float
    maximum_volume: float

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("Symbol must not be empty.")

        if self.contract_size <= 0:
            raise ValueError(
                "Contract size must be greater than zero."
            )

        if self.tick_size <= 0:
            raise ValueError(
                "Tick size must be greater than zero."
            )

        if self.tick_value <= 0:
            raise ValueError(
                "Tick value must be greater than zero."
            )

        if self.volume_step <= 0:
            raise ValueError(
                "Volume step must be greater than zero."
            )

        if self.minimum_volume <= 0:
            raise ValueError(
                "Minimum volume must be greater than zero."
            )

        if self.maximum_volume < self.minimum_volume:
            raise ValueError(
                "Maximum volume cannot be less than minimum volume."
            )