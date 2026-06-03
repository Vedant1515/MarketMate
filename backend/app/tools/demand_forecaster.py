import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import get_settings


logger = logging.getLogger(__name__)

_sales_df: Optional[pd.DataFrame] = None


def _load_sales_data() -> pd.DataFrame:
    global _sales_df
    if _sales_df is None:
        settings = get_settings()
        _sales_df = pd.read_csv(settings.sales_data_path, parse_dates=["date"])
    return _sales_df


def invalidate_cache() -> None:
    global _sales_df
    _sales_df = None


def _weekly_totals(df: pd.DataFrame, item: str) -> pd.DataFrame:
    item_df = df[df["item"].str.lower() == item.lower()].copy()
    if item_df.empty:
        item_df = df[df["item"].str.lower().str.contains(item.lower(), na=False)].copy()
    if item_df.empty:
        return pd.DataFrame()
    weekly = (
        item_df.groupby("week_number")
        .agg(
            total_qty=("quantity_sold", "sum"),
            daily_avg=("quantity_sold", "mean"),
            revenue=("revenue_aud", "sum"),
            unit_price=("unit_price_aud", "mean"),
            unit=("unit", "first"),
            trend=("trend", "last"),
            has_holiday=("is_public_holiday", "max"),
            has_pre_holiday=("is_pre_holiday", "max"),
        )
        .reset_index()
        .sort_values("week_number")
    )
    return weekly


def _linear_trend(x: np.ndarray, y: np.ndarray) -> tuple:
    if len(x) < 2:
        return 0.0, float(y[0]) if len(y) > 0 else 0.0
    coeffs = np.polyfit(x, y, 1)
    return float(coeffs[0]), float(coeffs[1])


def _confidence_label(cv: float, n_weeks: int) -> str:
    if n_weeks < 4:
        return "Low"
    if cv < 0.12 and n_weeks >= 6:
        return "High"
    if cv < 0.25:
        return "Medium"
    return "Low"


def forecast_item(item_name: str, weeks_ahead: int = 1) -> Dict[str, Any]:
    try:
        df = _load_sales_data()
    except Exception as exc:
        return {"error": str(exc)}

    weekly = _weekly_totals(df, item_name)
    if weekly.empty:
        return {"error": f"No data found for '{item_name}'"}

    actual_item = df[df["item"].str.lower() == item_name.lower()]["item"].iloc[0] if not df[df["item"].str.lower() == item_name.lower()].empty else item_name
    unit = weekly["unit"].iloc[0]
    n = len(weekly)

    qty_array = weekly["total_qty"].values.astype(float)
    week_array = weekly["week_number"].values.astype(float)

    # Linear regression trend
    slope, intercept = _linear_trend(week_array, qty_array)
    next_week_num = float(week_array[-1]) + weeks_ahead
    linear_forecast = slope * next_week_num + intercept

    # Rolling averages
    roll_4 = float(qty_array[-4:].mean()) if n >= 4 else float(qty_array.mean())
    roll_8 = float(qty_array[-8:].mean()) if n >= 8 else float(qty_array.mean())

    # Weighted blend: more recent data weighted higher
    if n >= 8:
        blended = 0.35 * linear_forecast + 0.40 * roll_4 + 0.25 * roll_8
    elif n >= 4:
        blended = 0.40 * linear_forecast + 0.60 * roll_4
    else:
        blended = linear_forecast

    blended = max(0.0, blended)

    # Coefficient of variation for confidence
    cv = float(np.std(qty_array[-4:]) / np.mean(qty_array[-4:])) if n >= 4 and np.mean(qty_array[-4:]) > 0 else 1.0
    confidence = _confidence_label(cv, n)

    # Trend classification
    if slope > qty_array.mean() * 0.02:
        trend_dir = "rising"
    elif slope < -qty_array.mean() * 0.02:
        trend_dir = "declining"
    else:
        trend_dir = "stable"

    # Week-over-week change
    if n >= 2:
        wow_pct = (qty_array[-1] - qty_array[-2]) / max(qty_array[-2], 1) * 100
    else:
        wow_pct = 0.0

    # Upper/lower bounds (1 std dev of recent weeks)
    std_recent = float(np.std(qty_array[-4:])) if n >= 4 else float(np.std(qty_array))
    upper = blended + std_recent
    lower = max(0.0, blended - std_recent)

    return {
        "item": actual_item,
        "unit": unit,
        "weeks_of_data": n,
        "predicted_weekly_qty": round(blended, 1),
        "predicted_daily_avg": round(blended / 7, 1),
        "lower_bound": round(lower, 1),
        "upper_bound": round(upper, 1),
        "confidence": confidence,
        "trend_direction": trend_dir,
        "trend_slope_per_week": round(slope, 2),
        "rolling_avg_4w": round(roll_4, 1),
        "rolling_avg_8w": round(roll_8, 1) if n >= 8 else None,
        "wow_change_pct": round(wow_pct, 1),
        "last_week_qty": round(float(qty_array[-1]), 1),
        "peak_week_qty": round(float(qty_array.max()), 1),
        "season_position": "early" if next_week_num <= 4 else "mid" if next_week_num <= 8 else "late",
    }


def demand_forecaster_tool(item_names: str) -> str:
    logger.info("demand_forecaster_tool called for: %s", item_names)

    items = [i.strip() for i in item_names.split(",") if i.strip()]
    if not items:
        items = ["Bananas", "Avocados", "Tomatoes", "Strawberries", "Spinach"]

    lines = ["=== Demand Forecast (Data-Driven Prediction) ===\n"]

    for item in items:
        result = forecast_item(item)
        if "error" in result:
            lines.append(f"{item}: {result['error']}\n")
            continue

        conf_symbol = {"High": "***", "Medium": "**", "Low": "*"}.get(result["confidence"], "*")
        trend_symbol = {"rising": "+", "declining": "-", "stable": "~"}.get(result["trend_direction"], "~")

        lines.append(f"--- {result['item']} ({result['unit']}) {conf_symbol} confidence: {result['confidence']} ---")
        lines.append(f"  Predicted next week: {result['predicted_weekly_qty']} {result['unit']} (range: {result['lower_bound']}-{result['upper_bound']})")
        lines.append(f"  Predicted daily avg: {result['predicted_daily_avg']} {result['unit']}/day")
        lines.append(f"  Trend: {trend_symbol} {result['trend_direction']} ({result['trend_slope_per_week']:+.1f} {result['unit']}/week slope)")
        lines.append(f"  Last week actual: {result['last_week_qty']} | 4-week avg: {result['rolling_avg_4w']}")
        if result["rolling_avg_8w"]:
            lines.append(f"  8-week avg: {result['rolling_avg_8w']} | Week-over-week: {result['wow_change_pct']:+.1f}%")
        lines.append(f"  Based on {result['weeks_of_data']} weeks of data")
        lines.append("")

    lines.append("Note: forecast accuracy improves with more historical data. Confidence is LOW with under 4 weeks.")
    return "\n".join(lines)
