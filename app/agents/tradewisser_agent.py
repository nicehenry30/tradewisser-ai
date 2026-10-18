import json
import re

from app.services.llm_service import LLMService
from app.tools.registry import ToolRegistry


def normalize_financial_numbers(text: str) -> str:
    """
    Normalize common financial number formatting before
    sending the user's request to the LLM.

    Examples:

        $10,000     -> USD 10000
        $1,500.50   -> USD 1500.50
        ₦500,000    -> NGN 500000
        €2,000      -> EUR 2000
        £1,250      -> GBP 1250
    """

    currency_symbols = {
        "$": "USD",
        "₦": "NGN",
        "€": "EUR",
        "£": "GBP",
    }

    normalized_text = text

    for symbol, currency in currency_symbols.items():

        pattern = re.compile(
            rf"{re.escape(symbol)}\s*"
            rf"((?:\d{{1,3}}(?:,\d{{3}})+)|"
            rf"\d+)"
            rf"(?:\.(\d+))?"
        )

        def replace_currency(match):
            whole_number = match.group(1).replace(",", "")
            decimal_part = match.group(2)

            if decimal_part:
                number = f"{whole_number}.{decimal_part}"
            else:
                number = whole_number

            return f"{currency} {number}"

        normalized_text = pattern.sub(
            replace_currency,
            normalized_text,
        )

    return normalized_text


class TradewisserAgent:

    def __init__(self):
        self.llm = LLMService()

    def respond(self, user_message: str):

        normalized_message = normalize_financial_numbers(
            user_message
        )

        system_prompt = (
            "You are Tradewisser AI, an intelligent trading assistant. "
            "You help traders understand financial markets, trading concepts, "
            "risk management, trading psychology, and trading strategies. "
            "You provide educational and analytical information. "
            "You do not guarantee profits or present uncertain information "
            "as guaranteed financial advice."
        )

        tools = ToolRegistry.get_tools()

        prompt = f"""
{system_prompt}

Tool usage rules:

1. When the user asks for a precise risk calculation,
   you MUST use the calculate_risk tool.

2. When the user asks for a precise position-size calculation,
   you MUST use the calculate_position_size tool.

3. When the user asks for the current, latest, or live price
   of a trading instrument, you MUST use the get_market_price tool.

4. When the user asks about recent price movement, candle data,
   market structure, trend, support/resistance, or technical analysis
   that requires historical price data, you MUST use the
   get_market_candles tool.

5. Never invent, estimate, or assume a current market price.
   Current market prices must come from the get_market_price tool.

6. Never invent historical OHLC prices.
   Historical market data must come from the get_market_candles tool.

7. When using market candles, use an appropriate interval and
   number of candles for the user's request.

8. For position-size calculations, identify the trading symbol,
   risk amount, entry price, and stop-loss price from the user's message.

9. If the user provides an account balance and risk percentage,
   calculate the monetary risk using calculate_risk first.

10. If calculate_risk returns a risk amount and the user has also
    provided the symbol, entry price, and stop-loss price, use that
    risk amount with calculate_position_size.

11. Do NOT invent instrument specifications such as tick size,
    tick value, contract size, minimum volume, or volume step.
    Those values are retrieved internally by Tradewisser.

12. If the requested instrument is not supported, clearly explain
    that Tradewisser does not currently have a trusted specification
    for that instrument.

13. Do not perform precise financial calculations yourself when
    an appropriate calculation tool is available.

14. When analyzing market candles, clearly distinguish between
    observations supported by the retrieved data and uncertainty.
    Do not present a market interpretation as a guaranteed outcome.

15. Financial numbers may have currency symbols and thousands
    separators. Interpret them correctly.

16. The normalized user message below has already had common
    currency formatting normalized.

17. Before asking the user for missing information, inspect the
    entire normalized user message and extract all clearly stated values.

Normalized user message:
{normalized_message}
"""

        conversation = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        max_tool_rounds = 10

        for _ in range(max_tool_rounds):

            response = self.llm.ask(
                conversation,
                tools=tools,
                tool_choice="auto",
            )

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                return response.output_text

            conversation.extend(response.output)

            for item in function_calls:

                try:
                    arguments = json.loads(
                        item.arguments
                    )

                    result = ToolRegistry.execute(
                        item.name,
                        arguments,
                    )

                    tool_output = {
                        "result": result
                    }

                except Exception as exc:

                    tool_output = {
                        "error": str(exc)
                    }

                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(
                            tool_output
                        ),
                    }
                )

        raise RuntimeError(
            "Tradewisser AI exceeded the maximum number "
            "of tool-calling rounds."
        )