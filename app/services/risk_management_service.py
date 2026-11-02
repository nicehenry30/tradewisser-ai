class RiskManagementService:
    """
    Coordinates risk-policy validation, monetary risk calculation,
    instrument lookup, and position-size calculation.

    This service does not create trade proposals or execute trades.
    """

    def __init__(
        self,
        risk_policy,
        risk_calculator,
        instrument_service,
        position_size_calculator,
    ):
        self.risk_policy = risk_policy
        self.risk_calculator = risk_calculator
        self.instrument_service = instrument_service
        self.position_size_calculator = (
            position_size_calculator
        )

    def calculate(
        self,
        symbol,
        account_balance,
        risk_percent,
        entry_price,
        stop_loss_price,
    ):
        self.risk_policy.validate(
            account_balance=account_balance,
            risk_percent=risk_percent,
        )

        risk_amount = (
            self.risk_calculator.calculate_risk_amount(
                account_balance=account_balance,
                risk_percent=risk_percent,
            )
        )

        instrument = (
            self.instrument_service.get_instrument(
                symbol
            )
        )

        position_size = (
            self.position_size_calculator.calculate_position_size(
                risk_amount=risk_amount,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                instrument=instrument,
            )
        )

        return {
            "symbol": symbol,
            "risk_percent": risk_percent,
            "risk_amount": risk_amount,
            "position_size": position_size,
        }