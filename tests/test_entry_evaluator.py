from app.strategy.entry import EntryEvaluator


def test_entry_is_authorized_when_all_required_confirmations_exist():
    evaluator = EntryEvaluator()

    result = evaluator.evaluate(
        direction="bullish",
        setup_qualified=True,
        facts={
            "five_minute_confirmed": True,
            "one_minute_confirmed": True,
        },
    )

    assert result.entry_authorized is True
    assert result.confirmations == [
        "qualified_setup",
        "5m_confirmation",
        "1m_confirmation",
    ]
    assert result.contradictions == []


def test_entry_is_not_authorized_without_setup():
    evaluator = EntryEvaluator()

    result = evaluator.evaluate(
        direction="bullish",
        setup_qualified=False,
        facts={
            "five_minute_confirmed": True,
            "one_minute_confirmed": True,
        },
    )

    assert result.entry_authorized is False
    assert "setup_not_qualified" in result.contradictions


def test_entry_is_not_authorized_without_5m_confirmation():
    evaluator = EntryEvaluator()

    result = evaluator.evaluate(
        direction="bullish",
        setup_qualified=True,
        facts={
            "five_minute_confirmed": False,
            "one_minute_confirmed": True,
        },
    )

    assert result.entry_authorized is False
    assert "5m_confirmation_missing" in result.contradictions


def test_entry_is_not_authorized_without_1m_confirmation():
    evaluator = EntryEvaluator()

    result = evaluator.evaluate(
        direction="bullish",
        setup_qualified=True,
        facts={
            "five_minute_confirmed": True,
            "one_minute_confirmed": False,
        },
    )

    assert result.entry_authorized is False
    assert "1m_confirmation_missing" in result.contradictions


def test_entry_evaluation_rejects_invalid_direction():
    evaluator = EntryEvaluator()

    try:
        evaluator.evaluate(
            direction="sideways",
            setup_qualified=True,
            facts={
                "five_minute_confirmed": True,
                "one_minute_confirmed": True,
            },
        )
    except ValueError as exc:
        assert str(exc) == (
            "Direction must be 'bullish' or 'bearish'."
        )
    else:
        raise AssertionError(
            "Expected invalid direction to raise ValueError."
        )