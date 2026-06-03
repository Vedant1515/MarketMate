from unittest.mock import MagicMock, patch

import pytest

from app.tools.holiday_checker import holiday_checker_tool
from app.tools.spoilage_scorer import spoilage_scorer_tool, _sales_df


def test_holiday_checker_queens_birthday():
    result = holiday_checker_tool("2026-06-08")
    assert "Queen's Birthday" in result
    assert "LOW TRADE DAY" in result


def test_holiday_checker_queens_birthday_eve():
    result = holiday_checker_tool("2026-06-07")
    assert "Queen's Birthday" in result or "eve" in result.lower()
    assert "HIGH TRADE DAY" in result or "high" in result.lower()


def test_holiday_checker_next_7_days_returns_string():
    result = holiday_checker_tool("next 7 days")
    assert isinstance(result, str)
    assert len(result) > 10


def test_holiday_checker_invalid_date():
    result = holiday_checker_tool("not-a-date")
    assert "Could not parse" in result


def test_holiday_checker_no_holiday():
    result = holiday_checker_tool("2026-07-15")
    assert "No public holidays" in result or "Normal ordering" in result


def test_holiday_checker_christmas():
    result = holiday_checker_tool("2026-12-25")
    assert "Christmas" in result
    assert "LOW TRADE DAY" in result


def test_holiday_checker_good_friday_eve():
    result = holiday_checker_tool("2026-04-02")
    assert "Maundy Thursday" in result or "Good Friday" in result


def test_spoilage_scorer_unknown_item():
    import app.tools.spoilage_scorer as ss
    ss._sales_df = None
    with patch("app.tools.spoilage_scorer._load_sales_data") as mock_load:
        import pandas as pd
        mock_load.return_value = pd.DataFrame({
            "item": ["Bananas", "Bananas"],
            "week_number": [1, 2],
            "quantity_sold": [100.0, 110.0],
            "spoilage_days": [7, 7],
            "trend": ["stable", "rising"],
            "unit": ["kg", "kg"],
            "date": pd.to_datetime(["2026-04-01", "2026-04-08"]),
        })
        result = spoilage_scorer_tool("Unicorn Fruit")
        assert "No sales data found" in result


def test_spoilage_scorer_short_shelf_declining():
    import app.tools.spoilage_scorer as ss
    ss._sales_df = None
    with patch("app.tools.spoilage_scorer._load_sales_data") as mock_load:
        import pandas as pd
        mock_load.return_value = pd.DataFrame({
            "item": ["Strawberries"] * 6,
            "week_number": [1, 1, 1, 2, 2, 2],
            "quantity_sold": [80.0, 60.0, 50.0, 40.0, 30.0, 25.0],
            "spoilage_days": [3] * 6,
            "trend": ["declining"] * 6,
            "unit": ["punnet"] * 6,
            "date": pd.to_datetime([
                "2026-04-01", "2026-04-02", "2026-04-03",
                "2026-04-08", "2026-04-09", "2026-04-10",
            ]),
        })
        result = spoilage_scorer_tool("Strawberries")
        assert "Strawberries" in result
        risk_line = [l for l in result.split("\n") if "Risk Level:" in l]
        assert len(risk_line) > 0
        risk = risk_line[0].split(":")[-1].strip()
        assert risk in ("High", "Critical")


def test_spoilage_scorer_long_shelf_stable():
    import app.tools.spoilage_scorer as ss
    ss._sales_df = None
    with patch("app.tools.spoilage_scorer._load_sales_data") as mock_load:
        import pandas as pd
        mock_load.return_value = pd.DataFrame({
            "item": ["Potatoes"] * 4,
            "week_number": [1, 1, 2, 2],
            "quantity_sold": [200.0, 210.0, 205.0, 215.0],
            "spoilage_days": [21] * 4,
            "trend": ["stable"] * 4,
            "unit": ["kg"] * 4,
            "date": pd.to_datetime([
                "2026-04-01", "2026-04-02",
                "2026-04-08", "2026-04-09",
            ]),
        })
        result = spoilage_scorer_tool("Potatoes")
        assert "Potatoes" in result
        risk_line = [l for l in result.split("\n") if "Risk Level:" in l]
        assert len(risk_line) > 0
        risk = risk_line[0].split(":")[-1].strip()
        assert risk in ("Low", "Medium")
