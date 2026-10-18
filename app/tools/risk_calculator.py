class RiskCalculator:

    @staticmethod
    def calculate_risk_amount(
        account_balance: float,
        risk_percent: float,
    ) -> float:
        """
        Calculate the maximum monetary amount
        a trader is willing to risk.

        Example:
        Account balance = 10,000
        Risk = 1%

        Maximum risk = 100
        """

        if account_balance <= 0:
            raise ValueError("Account balance must be greater than zero.")

        if risk_percent <= 0:
            raise ValueError("Risk percentage must be greater than zero.")

        if risk_percent > 100:
            raise ValueError("Risk percentage cannot exceed 100.")

        return round(
            account_balance * (risk_percent / 100),
            2,
        )