from app.agents.tradewisser_agent import TradewisserAgent


def main():
    agent = TradewisserAgent()

    response = agent.respond(
        "I want to trade XAUUSD. "
        "I am willing to risk $100. "
        "My entry price is 2000 and my stop loss is 1990. "
        "What position size should I use?"
    )

    print("\nTradewisser AI:")
    print(response)


if __name__ == "__main__":
    main()