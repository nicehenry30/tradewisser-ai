from app.models.trade_decision import TradeDecision
from app.services.llm_service import LLMService


def main():
    llm = LLMService()

    response = llm.ask_structured(
        input=[
            {
                "role": "system",
                "content": (
                    "You are a trading analysis assistant. "
                    "Return a structured trading decision."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze this example: XAUUSD is trading around 2000. "
                    "Assume a hypothetical bullish setup with an entry at 2000, "
                    "stop loss at 1990, take profit at 2020, "
                    "and confidence of 78."
                ),
            },
        ],
        text_format=TradeDecision,
    )

    decision = response.output_parsed

    print("\nStructured Tradewisser Decision:")
    print(decision)

    print("\nAs dictionary:")
    print(decision.model_dump())


if __name__ == "__main__":
    main()