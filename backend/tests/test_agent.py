import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.demo.responses import DEMO_RESPONSES
from app.routes.chat import _find_demo_key, _normalise_query


def test_normalise_query_strips_punctuation():
    assert _normalise_query("What should I order this Monday?") == "what should i order this monday"
    assert _normalise_query("  hello world.  ") == "hello world"


def test_find_demo_key_exact_match():
    key = _find_demo_key("what should i order this monday")
    assert key == "what should i order this monday"


def test_find_demo_key_case_insensitive():
    key = _find_demo_key("What Should I Order This Monday")
    assert key == "what should i order this monday"


def test_find_demo_key_with_question_mark():
    key = _find_demo_key("what should i order this monday?")
    assert key == "what should i order this monday"


def test_find_demo_key_fuzzy_match():
    key = _find_demo_key("are strawberries worth ordering in june")
    assert key is not None


def test_find_demo_key_no_match():
    key = _find_demo_key("tell me about the weather")
    assert key is None


def test_demo_responses_structure():
    required_keys = {
        "what should i order this monday",
        "are strawberries still worth ordering in june",
        "queens birthday is next week how do i adjust",
        "we have leftover strawberries from friday what do we do",
        "should i order mangoes this week",
        "which items have been our best performers this month",
    }
    assert set(DEMO_RESPONSES.keys()) == required_keys


def test_demo_responses_have_required_fields():
    for key, demo in DEMO_RESPONSES.items():
        assert "trace" in demo, f"Missing 'trace' in demo key: {key}"
        assert "tokens" in demo, f"Missing 'tokens' in demo key: {key}"
        assert "order" in demo, f"Missing 'order' in demo key: {key}"
        assert isinstance(demo["trace"], list)
        assert isinstance(demo["tokens"], str)
        assert len(demo["tokens"]) > 50


def test_monday_and_queens_birthday_have_orders():
    monday_demo = DEMO_RESPONSES["what should i order this monday"]
    assert monday_demo["order"] is not None
    assert "items" in monday_demo["order"]
    assert len(monday_demo["order"]["items"]) > 0

    qb_demo = DEMO_RESPONSES["queens birthday is next week how do i adjust"]
    assert qb_demo["order"] is not None
    assert "items" in qb_demo["order"]


def test_seasonal_demos_have_no_order():
    assert DEMO_RESPONSES["are strawberries still worth ordering in june"]["order"] is None
    assert DEMO_RESPONSES["should i order mangoes this week"]["order"] is None


def test_trace_steps_have_correct_fields():
    for key, demo in DEMO_RESPONSES.items():
        for step in demo["trace"]:
            assert "tool_name" in step, f"Missing tool_name in trace for {key}"
            assert "input" in step, f"Missing input in trace for {key}"
            assert "output" in step, f"Missing output in trace for {key}"
            assert "timestamp" in step, f"Missing timestamp in trace for {key}"
            assert step["tool_name"] in (
                "sales_retriever", "holiday_checker",
                "spoilage_scorer", "order_generator"
            ), f"Unknown tool_name in {key}: {step['tool_name']}"
