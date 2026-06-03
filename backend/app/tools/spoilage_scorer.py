import logging
from typing import Optional

import pandas as pd

from app.config import get_settings


logger = logging.getLogger(__name__)

_sales_df: Optional[pd.DataFrame] = None


def _load_sales_data() -> pd.DataFrame:
    global _sales_df
    if _sales_df is None:
        settings = get_settings()
        try:
            _sales_df = pd.read_csv(settings.sales_data_path, parse_dates=["date"])
            logger.info("spoilage_scorer loaded sales data: %d rows", len(_sales_df))
        except Exception as exc:
            logger.error("spoilage_scorer failed to load sales data: %s", exc)
            raise
    return _sales_df


def _risk_level(ratio: float, trend: str, spoilage_days: int) -> str:
    if spoilage_days >= 14:
        if ratio > 0.9:
            return "Medium"
        return "Low"
    if spoilage_days <= 3:
        if trend == "declining":
            if ratio > 0.6:
                return "Critical"
            return "High"
        if ratio > 0.8:
            return "High"
        if ratio > 0.5:
            return "Medium"
        return "Low"
    # 4-13 days spoilage window
    if trend == "declining":
        if ratio > 0.75:
            return "High"
        if ratio > 0.5:
            return "Medium"
        return "Low"
    if ratio > 0.85:
        return "High"
    if ratio > 0.6:
        return "Medium"
    return "Low"


def _recommended_action(risk: str, item: str, trend: str, daily_avg: float, unit: str) -> str:
    actions = {
        "Critical": (
            f"URGENT: Mark down {item} immediately. "
            f"Daily sales avg is {daily_avg:.1f} {unit} but stock is aging fast. "
            "Consider 30-40% discount or bundle deal today. Do not reorder until current stock clears."
        ),
        "High": (
            f"Reduce next order of {item} by 25-35%. "
            f"Current trend is {trend} - you are likely to have waste. "
            "Prioritise selling through existing stock before placing new order."
        ),
        "Medium": (
            f"{item} has moderate spoilage risk. "
            f"Monitor daily velocity closely. If sales are below {daily_avg:.1f} {unit}/day "
            "by midweek, consider reducing the next order."
        ),
        "Low": (
            f"{item} is within normal parameters. "
            f"Spoilage risk is low. Order as per normal schedule at or near average {daily_avg:.1f} {unit}/day."
        ),
    }
    return actions.get(risk, f"Monitor {item} closely.")


def spoilage_scorer_tool(item_name: str) -> str:
    logger.info("spoilage_scorer_tool called for item: %s", item_name)

    try:
        df = _load_sales_data()
    except Exception as exc:
        return f"Error loading sales data: {exc}"

    item_df = df[df["item"].str.lower() == item_name.lower()]
    if item_df.empty:
        # Try partial match
        item_df = df[df["item"].str.lower().str.contains(item_name.lower(), na=False)]
        if item_df.empty:
            return (
                f"No sales data found for '{item_name}'. "
                "Check the item name and try again."
            )

    actual_item = item_df["item"].iloc[0]
    max_week = item_df["week_number"].max()
    recent_df = item_df[item_df["week_number"] == max_week]

    spoilage_days = int(recent_df["spoilage_days"].iloc[0])
    trend = str(recent_df["trend"].iloc[0])
    unit = str(recent_df["unit"].iloc[0])

    daily_sales = recent_df["quantity_sold"].tolist()
    daily_avg = sum(daily_sales) / len(daily_sales) if daily_sales else 0.0
    total_recent = sum(daily_sales)
    days_in_week = len(daily_sales)

    # days_elapsed since last order - assume mid-week assessment (3 days in)
    days_elapsed = min(3, spoilage_days)
    ratio = days_elapsed / spoilage_days if spoilage_days > 0 else 1.0

    # Adjust ratio based on declining trend
    if trend == "declining":
        ratio = min(ratio * 1.3, 1.0)

    risk = _risk_level(ratio, trend, spoilage_days)
    action = _recommended_action(risk, actual_item, trend, daily_avg, unit)

    # Sales velocity check
    recent_trend_pct = 0.0
    if max_week > 1:
        prev_df = item_df[item_df["week_number"] == max_week - 1]
        if not prev_df.empty:
            prev_avg = prev_df["quantity_sold"].mean()
            if prev_avg > 0:
                recent_trend_pct = ((daily_avg - prev_avg) / prev_avg) * 100

    output_lines = [
        f"=== Spoilage Risk Assessment: {actual_item} ===",
        f"Risk Level: {risk}",
        f"Spoilage window: {spoilage_days} days",
        f"Current trend: {trend} (velocity change: {recent_trend_pct:+.1f}% vs prev week)",
        f"Recent daily average: {daily_avg:.1f} {unit}/day (week {int(max_week)} - {days_in_week} days)",
        f"Total sold this week so far: {total_recent:.1f} {unit}",
        f"Spoilage risk ratio: {ratio:.2f} (days elapsed / spoilage window)",
        f"",
        f"Recommended action: {action}",
    ]
    return "\n".join(output_lines)
