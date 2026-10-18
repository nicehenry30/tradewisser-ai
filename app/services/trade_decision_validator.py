from app.models.trade_proposal import TradeProposal


class TradeDecisionValidator:
    """
    Performs deterministic validation of an AI-generated trade proposal.

    The AI proposes the trade.
    This validator determines whether the price structure is logically valid.
    """

    @staticmethod
    def validate_price_structure(proposal: TradeProposal) -> list[str]:
        """
        Validate the relationship between entry, stop loss,
        and take profit.

        Returns a list of validation errors.
        An empty list means the price structure passed validation.
        """

        errors: list[str] = []

        # WAIT does not represent an executable trade.
        if proposal.direction == "WAIT":
            return errors

        # An executable BUY or SELL proposal requires all three prices.
        if proposal.entry is None:
            errors.append("Entry price is required.")

        if proposal.stop_loss is None:
            errors.append("Stop-loss price is required.")

        if proposal.take_profit is None:
            errors.append("Take-profit price is required.")

        # Do not perform comparisons until all prices exist.
        if errors:
            return errors

        entry = proposal.entry
        stop_loss = proposal.stop_loss
        take_profit = proposal.take_profit

        if proposal.direction == "BUY":
            if stop_loss >= entry:
                errors.append(
                    "For a BUY trade, stop-loss must be below entry."
                )

            if take_profit <= entry:
                errors.append(
                    "For a BUY trade, take-profit must be above entry."
                )

        elif proposal.direction == "SELL":
            if stop_loss <= entry:
                errors.append(
                    "For a SELL trade, stop-loss must be above entry."
                )

            if take_profit >= entry:
                errors.append(
                    "For a SELL trade, take-profit must be below entry."
                )

        return errors