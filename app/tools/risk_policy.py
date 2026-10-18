class RiskPolicy:

    def __init__(
        self,
        maximum_risk_percent: float = 2.0,
    ):
        if maximum_risk_percent <= 0:
            raise ValueError(
                "Maximum risk percentage must be greater than zero."
            )

        if maximum_risk_percent > 100:
            raise ValueError(
                "Maximum risk percentage cannot exceed 100."
            )

        self.maximum_risk_percent = maximum_risk_percent

    def validate(
        self,
        account_balance: float,
        risk_percent: float,
    ) -> None:
        """
        Validate that a requested trade risk
        is within the configured maximum risk limit.
        """

        if account_balance <= 0:
            raise ValueError(
                "Account balance must be greater than zero."
            )

        if risk_percent <= 0:
            raise ValueError(
                "Risk percentage must be greater than zero."
            )

        if risk_percent > self.maximum_risk_percent:
            raise ValueError(
                f"Requested risk of {risk_percent}% exceeds "
                f"the maximum allowed risk of "
                f"{self.maximum_risk_percent}%."
            )