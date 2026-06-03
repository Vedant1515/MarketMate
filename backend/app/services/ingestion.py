import logging
import os
from typing import Dict, List

import pandas as pd

from app.services.vector_store import VectorStore


logger = logging.getLogger(__name__)


def _trend_label(pct_change: float) -> str:
    if pct_change > 5:
        return "rising"
    if pct_change < -5:
        return "declining"
    return "stable"


def _season_label(trend: str, week_number: int) -> str:
    if trend == "rising":
        return "rising"
    if trend == "declining":
        return "declining"
    return "stable"


def _build_document(row: pd.Series, prev_qty: float) -> str:
    pct_vs_prev = 0.0
    if prev_qty and prev_qty > 0:
        pct_vs_prev = ((row["total_qty"] - prev_qty) / prev_qty) * 100

    date_range = f"{row['min_date']} to {row['max_date']}"
    trend_str = _trend_label(pct_vs_prev)
    season_str = _season_label(row["trend"], int(row["week_number"]))
    margin = row["revenue"] * 0.65

    lines = [
        f"Week {int(row['week_number'])}: {row['item']} ({date_range})",
        (
            f"Total qty sold: {row['total_qty']:.1f} {row['unit']} | "
            f"Daily avg: {row['daily_avg']:.1f} | "
            f"Peak day: {row['peak_day']} ({row['peak_qty']:.1f} {row['unit']})"
        ),
        (
            f"Trend: {trend_str} ({pct_vs_prev:+.1f}% vs prev week) | "
            f"Spoilage window: {int(row['spoilage_days'])} days"
        ),
        (
            f"Public holiday week: {'yes' if row['has_holiday'] else 'no'} | "
            f"Pre-holiday week: {'yes' if row['has_pre_holiday'] else 'no'}"
        ),
        f"Revenue: ${row['revenue']:.2f} AUD | Estimated margin (65%): ${margin:.2f} AUD",
        f"Season status: {season_str}",
    ]
    return "\n".join(lines)


def run_ingestion(vector_store: VectorStore, sales_data_path: str) -> int:
    logger.info("Starting ingestion from %s", sales_data_path)

    if not os.path.exists(sales_data_path):
        logger.warning("Sales data file not found at %s - skipping ingestion", sales_data_path)
        return 0

    try:
        df = pd.read_csv(sales_data_path, parse_dates=["date"])
    except Exception as exc:
        logger.error("Failed to read CSV at %s: %s", sales_data_path, exc)
        raise

    required_cols = {
        "date", "week_number", "item", "unit", "quantity_sold",
        "unit_price_aud", "revenue_aud", "spoilage_days", "trend",
        "is_public_holiday", "is_pre_holiday",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    agg = (
        df.groupby(["week_number", "item"])
        .agg(
            total_qty=("quantity_sold", "sum"),
            daily_avg=("quantity_sold", "mean"),
            peak_qty=("quantity_sold", "max"),
            revenue=("revenue_aud", "sum"),
            unit=("unit", "first"),
            spoilage_days=("spoilage_days", "first"),
            trend=("trend", "last"),
            has_holiday=("is_public_holiday", "max"),
            has_pre_holiday=("is_pre_holiday", "max"),
            min_date=("date", "min"),
            max_date=("date", "max"),
        )
        .reset_index()
    )

    # Compute peak day name from the row with max quantity_sold per group
    peak_day_map: Dict = {}
    for (wk, item), grp in df.groupby(["week_number", "item"]):
        idx = grp["quantity_sold"].idxmax()
        peak_day_map[(wk, item)] = grp.loc[idx, "date"].day_name()

    agg["peak_day"] = agg.apply(
        lambda r: peak_day_map.get((r["week_number"], r["item"]), "Unknown"), axis=1
    )

    documents: List[Dict] = []
    for _, row in agg.iterrows():
        wk = int(row["week_number"])
        item_slug = row["item"].lower().replace(" ", "_")

        prev_rows = agg[
            (agg["week_number"] == wk - 1) & (agg["item"] == row["item"])
        ]
        prev_qty = float(prev_rows["total_qty"].iloc[0]) if not prev_rows.empty else 0.0

        doc_text = _build_document(row, prev_qty)
        doc_id = f"week_{wk}_{item_slug}"

        metadata: Dict = {
            "week_number": wk,
            "item": row["item"],
            "unit": row["unit"],
            "spoilage_days": int(row["spoilage_days"]),
            "trend": row["trend"],
            "total_qty": float(row["total_qty"]),
            "revenue": float(row["revenue"]),
            "has_holiday": int(row["has_holiday"]),
            "has_pre_holiday": int(row["has_pre_holiday"]),
        }

        documents.append({"id": doc_id, "text": doc_text, "metadata": metadata})

    vector_store.add_documents(documents)
    logger.info("Ingestion complete: %d documents added", len(documents))
    return len(documents)
