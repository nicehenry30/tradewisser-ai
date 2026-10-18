from app.models.instrument import InstrumentSpecification


class InstrumentService:
    """
    Provides validated trading specifications for instruments.

    This local registry is intentionally simple for now.
    Later, it can be replaced or extended with broker/MT4/MT5
    or market-data integrations.
    """

    _instruments = {
        "XAUUSD": InstrumentSpecification(
            symbol="XAUUSD",
            contract_size=100,
            tick_size=0.01,
            tick_value=1.0,
            volume_step=0.01,
            minimum_volume=0.01,
            maximum_volume=100.0,
        ),
    }

    @classmethod
    def get_instrument(
        cls,
        symbol: str,
    ) -> InstrumentSpecification:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError(
                "Instrument symbol must not be empty."
            )

        instrument = cls._instruments.get(
            normalized_symbol
        )

        if instrument is None:
            raise ValueError(
                f"Instrument '{normalized_symbol}' "
                "is not available."
            )

        return instrument

    @classmethod
    def list_instruments(cls) -> list[str]:
        return sorted(cls._instruments.keys())