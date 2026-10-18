from app.services.instrument_service import InstrumentService
from app.services.market_data_service import MarketDataService
from app.tools.position_size_calculator import PositionSizeCalculator
from app.tools.risk_calculator import RiskCalculator
from app.tools.risk_policy import RiskPolicy


class ToolRegistry:

    # Tradewisser's default maximum risk per trade.
    # This can later become configurable per user/account.
    risk_policy = RiskPolicy(
        maximum_risk_percent=2.0
    )

    @staticmethod
    def get_tools():
        return [
            {
                "type": "function",
                "name": "calculate_risk",
                "description": (
                    "Calculate the maximum monetary amount a trader "
                    "is willing to risk based on account balance "
                    "and risk percentage. The requested risk percentage "
                    "must comply with Tradewisser's risk policy."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_balance": {
                            "type": "number",
                            "description": "The trader's account balance.",
                        },
                        "risk_percent": {
                            "type": "number",
                            "description": (
                                "The percentage of the account "
                                "the trader wants to risk."
                            ),
                        },
                    },
                    "required": [
                        "account_balance",
                        "risk_percent",
                    ],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "calculate_position_size",
                "description": (
                    "Calculate the position size for a trading instrument "
                    "using the trader's risk amount, entry price, stop-loss "
                    "price, and the instrument's trusted trading specification. "
                    "The instrument specification is retrieved internally "
                    "and must not be supplied by the user or AI."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": (
                                "The trading instrument symbol, "
                                "for example XAUUSD."
                            ),
                        },
                        "risk_amount": {
                            "type": "number",
                            "description": (
                                "The maximum monetary amount the trader "
                                "is willing to lose."
                            ),
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "The trade entry price.",
                        },
                        "stop_loss_price": {
                            "type": "number",
                            "description": "The stop-loss price.",
                        },
                    },
                    "required": [
                        "symbol",
                        "risk_amount",
                        "entry_price",
                        "stop_loss_price",
                    ],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "get_market_price",
                "description": (
                    "Get the latest available market price for a trading "
                    "instrument from Tradewisser's configured market-data "
                    "provider. Never invent or estimate the current price."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": (
                                "The trading instrument symbol, for example "
                                "XAU/USD or XAUUSD."
                            ),
                        },
                    },
                    "required": [
                        "symbol",
                    ],
                    "additionalProperties": False,
                },
            },
            {
                "type": "function",
                "name": "get_market_candles",
                "description": (
                    "Retrieve recent OHLC market candles for a trading "
                    "instrument. Use this tool when the user asks about "
                    "recent price movement, candle data, market structure, "
                    "or technical analysis that requires historical price data."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": (
                                "The trading instrument symbol, for example "
                                "XAU/USD or XAUUSD."
                            ),
                        },
                        "interval": {
                            "type": "string",
                            "description": (
                                "The candle interval, for example "
                                "1min, 5min, 15min, 30min, 1h, or 1day."
                            ),
                        },
                        "outputsize": {
                            "type": "integer",
                            "description": (
                                "The number of recent candles to retrieve."
                            ),
                        },
                    },
                    "required": [
                        "symbol",
                    ],
                    "additionalProperties": False,
                },
            },
        ]

    @staticmethod
    def execute(
        tool_name: str,
        arguments: dict,
    ):

        if tool_name == "calculate_risk":

            ToolRegistry.risk_policy.validate(
                account_balance=arguments["account_balance"],
                risk_percent=arguments["risk_percent"],
            )

            return RiskCalculator.calculate_risk_amount(
                arguments["account_balance"],
                arguments["risk_percent"],
            )

        if tool_name == "calculate_position_size":

            instrument = InstrumentService.get_instrument(
                arguments["symbol"]
            )

            return PositionSizeCalculator.calculate_position_size(
                risk_amount=arguments["risk_amount"],
                entry_price=arguments["entry_price"],
                stop_loss_price=arguments["stop_loss_price"],
                instrument=instrument,
            )

        if tool_name == "get_market_price":

            market_data_service = MarketDataService()

            return market_data_service.get_price(
                arguments["symbol"]
            )

        if tool_name == "get_market_candles":

            market_data_service = MarketDataService()

            return market_data_service.get_candles(
                symbol=arguments["symbol"],
                interval=arguments.get("interval", "1h"),
                outputsize=arguments.get("outputsize", 20),
            )

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )