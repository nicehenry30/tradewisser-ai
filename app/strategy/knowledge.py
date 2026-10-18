from dataclasses import dataclass, field
from typing import Literal


RuleStatus = Literal["approved", "candidate"]
RuleSource = Literal["user_taught", "research_proposed"]


@dataclass(frozen=True)
class StrategyRule:
    """
    Represents a Tradewisser trading rule.

    A rule can be:
    - approved: part of the current Tradewisser methodology
    - candidate: proposed but not yet officially adopted
    """

    name: str
    category: str
    direction: str
    status: RuleStatus
    source: RuleSource

    core_principles: tuple[str, ...] = field(default_factory=tuple)
    strong_confirmations: tuple[str, ...] = field(default_factory=tuple)
    supporting_confirmations: tuple[str, ...] = field(default_factory=tuple)
    contradictions: tuple[str, ...] = field(default_factory=tuple)

    minimum_confirmations: int | None = None

    entry_timeframes: tuple[str, ...] = field(default_factory=tuple)
    context_timeframes: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# REVERSAL STRATEGY
# ---------------------------------------------------------------------------

REVERSAL_RULE = StrategyRule(
    name="reversal",
    category="reversal",
    direction="both",
    status="approved",
    source="user_taught",

    core_principles=(
        "Reversals are strongest at the top or bottom of important trading ranges.",
        "Previous day highs and lows are important support and resistance levels.",
        "Previous week highs and lows are very strong support and resistance levels.",
        "Multiple previous day highs or lows forming around the same price strengthen the level.",
        "Daily and weekly level confluence strengthens the reversal location.",
        "A level is a location for a potential reversal, not an automatic entry.",
        "The market must provide confirmation before entry.",
    ),

    strong_confirmations=(
        "bullish_or_bearish_momentum",
        "rejection",
        "double_top_or_double_bottom",
        "triple_top_or_triple_bottom",
        "pin_bar",
        "engulfing_candle",
        "lower_timeframe_structure",
        "daily_level_confluence",
        "weekly_level_confluence",
    ),

    supporting_confirmations=(
        "liquidity_sweep",
        "market_structure",
        "market_regime",
        "previous_day_high_or_low",
        "previous_week_high_or_low",
    ),

    contradictions=(
        "strong_opposing_market_structure",
        "insufficient_confirmation",
    ),

    minimum_confirmations=3,

    context_timeframes=(
        "weekly",
        "daily",
        "4h",
        "1h",
        "30m",
        "15m",
    ),

    entry_timeframes=(
        "5m",
        "1m",
    ),
)


# ---------------------------------------------------------------------------
# CONTINUATION STRATEGY
# ---------------------------------------------------------------------------

CONTINUATION_RULE = StrategyRule(
    name="continuation",
    category="continuation",
    direction="both",

    # This remains a candidate until the methodology is explicitly
    # approved as an official Tradewisser rule.
    status="candidate",
    source="research_proposed",

    core_principles=(
        "An established trend should remain structurally intact.",
        "Price should pull back within the established trend.",
        "The pullback should form a higher low in a bullish trend "
        "or a lower high in a bearish trend.",
        "Continuation structure should develop in the direction of the trend.",
        "A break of structure in the original trend direction can provide "
        "continuation confirmation.",
        "Entry should occur after the continuation structure provides confirmation.",
    ),

    strong_confirmations=(
        "trend_structure",
        "pullback",
        "higher_low",
        "lower_high",
        "break_of_structure",
        "lower_timeframe_confirmation",
    ),

    supporting_confirmations=(
        "support_or_resistance",
        "market_regime",
        "momentum",
    ),

    contradictions=(
        "trend_structure_failure",
        "strong_opposing_choch",
        "insufficient_confirmation",
    ),

    minimum_confirmations=3,

    context_timeframes=(
        "weekly",
        "daily",
        "4h",
        "1h",
        "30m",
        "15m",
    ),

    entry_timeframes=(
        "5m",
        "1m",
    ),
)


# ---------------------------------------------------------------------------
# TIMEFRAME POLICY
# ---------------------------------------------------------------------------

ENTRY_TIMEFRAME_POLICY = {
    "allowed_entry_timeframes": ("5m", "1m"),

    "context_timeframes": (
        "weekly",
        "daily",
        "4h",
        "1h",
        "30m",
        "15m",
    ),

    "principles": (
        "Higher timeframes establish market context.",
        "Higher timeframes establish the broader trading setup.",
        "5m and 1m are used for trade entry decisions.",
        "A higher timeframe setup alone must not generate the final entry.",
        "The entry layer should seek precise lower timeframe confirmation.",
        "The actual invalidation level determines stop placement.",
        "Risk management determines position size from the stop distance.",
    ),
}


# ---------------------------------------------------------------------------
# MARKET CONTEXT
# ---------------------------------------------------------------------------

MARKET_CONTEXT_PRINCIPLES = (
    "Market structure helps identify the current market context.",
    "BOS and CHOCH are part of understanding market context.",
    "Support and resistance provide location.",
    "Daily and weekly levels provide important market locations.",
    "The market regime should be identified as trending or ranging.",
    "The trading approach should adapt to the market regime.",
)


# ---------------------------------------------------------------------------
# RANGE MARKET PRINCIPLES
# ---------------------------------------------------------------------------

RANGE_MARKET_RULE = {
    "status": "approved",
    "source": "user_taught",

    "principles": (
        "In a ranging market, previous day high can be a potential "
        "bearish reversal location.",
        "In a ranging market, previous day low can be a potential "
        "bullish reversal location.",
        "A liquidity sweep can provide confirmation but is not mandatory.",
        "A rejection candle can provide confirmation but is not mandatory.",
        "A trade can be taken when enough requirements are satisfied.",
    ),

    "minimum_confirmations": 3,
}


# ---------------------------------------------------------------------------
# STRATEGY KNOWLEDGE REGISTRY
# ---------------------------------------------------------------------------

STRATEGY_RULES = {
    "reversal": REVERSAL_RULE,
    "continuation": CONTINUATION_RULE,
}


def get_strategy_rule(name: str) -> StrategyRule:
    """
    Return a strategy rule by name.
    """

    try:
        return STRATEGY_RULES[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown strategy rule: {name}"
        ) from exc


def get_approved_rules() -> tuple[StrategyRule, ...]:
    """
    Return only officially approved strategy rules.
    """

    return tuple(
        rule
        for rule in STRATEGY_RULES.values()
        if rule.status == "approved"
    )


def get_candidate_rules() -> tuple[StrategyRule, ...]:
    """
    Return strategy rules that are still candidates.
    """

    return tuple(
        rule
        for rule in STRATEGY_RULES.values()
        if rule.status == "candidate"
    )