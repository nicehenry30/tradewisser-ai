from typing import Any

from app.models.trade_proposal import (
    TakeProfitCandidate,
    TradeProposal,
)


class TradeProposalService:
    """
    Builds a deterministic trade proposal from an already-qualified
    15M setup and confirmed 5M entry layer.

    This service:
        - determines direction
        - uses the current price as the proposal entry
        - derives structural SL from higher-timeframe protected levels
        - applies an ATR buffer
        - identifies structural/reference TP candidates
        - calculates risk/reward

    This service does NOT:
        - calculate account risk
        - calculate position size
        - approve risk
        - execute trades
    """

    ATR_BUFFER_MULTIPLIER = 0.25

    def propose(
        self,
        symbol: str,
        fifteen_minute_setup: dict[str, Any],
        five_minute_confirmation: dict[str, Any],
        current_price: float,
        market_analysis: dict[str, Any],
        higher_timeframe_context: dict[str, Any],
    ) -> TradeProposal:

        setup_qualified = fifteen_minute_setup.get(
            "qualified",
            False,
        )

        confirmation_status = five_minute_confirmation.get(
            "status",
            "WAIT",
        )

        confirmation_direction = five_minute_confirmation.get(
            "thesis_direction",
            five_minute_confirmation.get(
                "direction",
                "neutral",
            ),
        )

        setup_direction = fifteen_minute_setup.get(
            "direction",
            "neutral",
        )

        if not setup_qualified:
            return self._wait_proposal(
                symbol=symbol,
                reason="15m setup is not qualified.",
            )

        if (
            confirmation_status != "CONFIRMED"
            or not five_minute_confirmation.get(
                "confirmed",
                False,
            )
        ):
            return self._wait_proposal(
                symbol=symbol,
                reason="5m confirmation is not complete.",
            )

        if confirmation_direction != setup_direction:
            return self._wait_proposal(
                symbol=symbol,
                reason="5m confirmation direction does not match the 15m thesis.",
            )

        if setup_direction not in {
            "bullish",
            "bearish",
        }:
            return self._wait_proposal(
                symbol=symbol,
                reason="Trade direction is not actionable.",
            )

        if current_price <= 0:
            return self._wait_proposal(
                symbol=symbol,
                reason="Current price is invalid.",
            )

        atr = self._get_atr(
            market_analysis
        )

        if atr <= 0:
            return self._wait_proposal(
                symbol=symbol,
                reason="ATR is unavailable or invalid.",
            )

        direction = (
            "BUY"
            if setup_direction == "bullish"
            else "SELL"
        )

        entry = float(current_price)

        stop_loss = self._calculate_stop_loss(
            direction=direction,
            entry=entry,
            atr=atr,
            context=higher_timeframe_context,
        )

        if stop_loss is None:
            return self._wait_proposal(
                symbol=symbol,
                reason="No valid structural stop-loss level is available.",
            )

        if direction == "BUY" and stop_loss >= entry:
            return self._wait_proposal(
                symbol=symbol,
                reason="Calculated BUY stop loss is not below entry.",
            )

        if direction == "SELL" and stop_loss <= entry:
            return self._wait_proposal(
                symbol=symbol,
                reason="Calculated SELL stop loss is not above entry.",
            )

        risk_distance = abs(
            entry - stop_loss
        )

        candidates = self._build_take_profit_candidates(
            direction=direction,
            entry=entry,
            risk_distance=risk_distance,
            context=higher_timeframe_context,
        )

        if not candidates:
            return self._wait_proposal(
                symbol=symbol,
                reason="No valid structural take-profit candidate is available.",
            )

        selected_target = candidates[0]

        reward_distance = abs(
            selected_target.price - entry
        )

        risk_reward_ratio = (
            reward_distance / risk_distance
            if risk_distance > 0
            else None
        )

        return TradeProposal(
            symbol=symbol,
            direction=direction,
            setup_family=fifteen_minute_setup.get(
                "setup_family"
            ),
            setup_type=fifteen_minute_setup.get(
                "setup_type"
            ),
            entry=entry,
            stop_loss=stop_loss,
            take_profit=selected_target.price,
            take_profit_candidates=candidates,
            risk_distance=risk_distance,
            reward_distance=reward_distance,
            risk_reward_ratio=risk_reward_ratio,
            entry_basis="current market price after confirmed 5m setup",
            stop_basis=(
                "higher-timeframe protected structure "
                "with ATR volatility buffer"
            ),
            confidence=0.0,
            market_regime=None,
            reasons=[
                "15m setup qualified",
                "5m confirmation aligned with 15m thesis",
                "entry derived from current market price",
                "stop derived from structural invalidation",
                "targets derived from existing higher-timeframe levels",
            ],
            warnings=[
                "Trade proposal is not risk-approved.",
                "Position size must be calculated by the Risk Engine.",
                "Execution must occur only after downstream risk approval.",
            ],
        )

    @staticmethod
    def _get_atr(
        market_analysis: dict[str, Any],
    ) -> float:
        try:
            return float(
                market_analysis.get(
                    "atr_14",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

    def _calculate_stop_loss(
        self,
        direction: str,
        entry: float,
        atr: float,
        context: dict[str, Any],
    ) -> float | None:

        buffer = atr * self.ATR_BUFFER_MULTIPLIER

        if direction == "BUY":
            structural_levels = [
                context.get(
                    "four_hour_protected_level"
                ),
                context.get(
                    "daily_protected_level"
                ),
                context.get(
                    "four_hour_major_support"
                ),
                context.get(
                    "daily_major_support"
                ),
            ]

            valid_levels = []

            for level in structural_levels:
                if level is None:
                    continue

                if isinstance(level, dict):
                    level = level.get("price")

                if level is None:
                    continue

                level = float(level)

                if level < entry:
                    valid_levels.append(level)

            if not valid_levels:
                return None

            structural_level = max(
                valid_levels
            )

            return structural_level - buffer

        if direction == "SELL":
            structural_levels = [
                context.get(
                    "four_hour_protected_level"
                ),
                context.get(
                    "daily_protected_level"
                ),
                context.get(
                    "four_hour_major_resistance"
                ),
                context.get(
                    "daily_major_resistance"
                ),
            ]

            valid_levels = []

            for level in structural_levels:
                if level is None:
                    continue

                if isinstance(level, dict):
                    level = level.get("price")

                if level is None:
                    continue

                level = float(level)

                if level > entry:
                    valid_levels.append(level)

            if not valid_levels:
                return None

            structural_level = min(
                valid_levels
            )

            return structural_level + buffer

        return None
    
    @staticmethod
    def _build_take_profit_candidates(
        direction: str,
        entry: float,
        risk_distance: float,
        context: dict[str, Any],
    ) -> list[TakeProfitCandidate]:

        if risk_distance <= 0:
            return []

        raw_candidates: list[
            tuple[float, str, str]
        ] = []

        if direction == "BUY":
            levels = [
                (
                    context.get(
                        "four_hour_major_resistance"
                    ),
                    "4h_structure",
                    "4H major resistance",
                ),
                (
                    context.get(
                        "daily_major_resistance"
                    ),
                    "1day_structure",
                    "Daily major resistance",
                ),
                (
                    context.get("pdh"),
                    "previous_day_reference",
                    "Previous Day High",
                ),
            ]

            for price, source, basis in levels:
                if (
                    price is not None
                    and float(price) > entry
                ):
                    raw_candidates.append(
                        (
                            float(price),
                            source,
                            basis,
                        )
                    )

        elif direction == "SELL":
            levels = [
                (
                    context.get(
                        "four_hour_major_support"
                    ),
                    "4h_structure",
                    "4H major support",
                ),
                (
                    context.get(
                        "daily_major_support"
                    ),
                    "1day_structure",
                    "Daily major support",
                ),
                (
                    context.get("pdl"),
                    "previous_day_reference",
                    "Previous Day Low",
                ),
            ]

            for price, source, basis in levels:
                if (
                    price is not None
                    and float(price) < entry
                ):
                    raw_candidates.append(
                        (
                            float(price),
                            source,
                            basis,
                        )
                    )

        # Remove duplicate prices.
        unique_candidates: dict[
            float,
            tuple[str, str],
        ] = {}

        for price, source, basis in raw_candidates:
            unique_candidates[price] = (
                source,
                basis,
            )

        ordered = sorted(
            unique_candidates.items(),
            key=lambda item: (
                item[0]
                if direction == "BUY"
                else -item[0]
            ),
        )

        return [
            TakeProfitCandidate(
                price=price,
                source=source,
                basis=basis,
                risk_reward_ratio=(
                    abs(price - entry)
                    / risk_distance
                ),
            )
            for price, (
                source,
                basis,
            ) in ordered
        ]

    @staticmethod
    def _wait_proposal(
        symbol: str,
        reason: str,
    ) -> TradeProposal:

        return TradeProposal(
            symbol=symbol,
            direction="WAIT",
            confidence=0.0,
            reasons=[],
            warnings=[reason],
        )