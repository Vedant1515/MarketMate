import logging
from typing import List

from app.services.vector_store import get_vector_store


logger = logging.getLogger(__name__)


def sales_retriever_tool(query: str) -> str:
    logger.info("sales_retriever_tool called with query: %s", query[:100])
    try:
        vs = get_vector_store()
        results = vs.query(query_text=query, n_results=4)
    except Exception as exc:
        logger.error("sales_retriever_tool failed: %s", exc)
        return f"Error retrieving sales data: {exc}"

    if not results:
        logger.warning("sales_retriever_tool returned no results for query: %s", query[:100])
        return "No historical sales data found for this query."

    lines: List[str] = ["=== Historical Sales Context (Manager Memory) ===\n"]
    for i, result in enumerate(results, start=1):
        text = result.get("text", "")
        meta = result.get("metadata", {})
        distance = result.get("distance", 1.0)
        relevance = max(0.0, 1.0 - float(distance))

        lines.append(f"--- Record {i} (relevance: {relevance:.2f}) ---")
        lines.append(text)

        week = meta.get("week_number", "?")
        item = meta.get("item", "?")
        unit = meta.get("unit", "?")
        total_qty = meta.get("total_qty", 0)
        trend = meta.get("trend", "unknown")
        revenue = meta.get("revenue", 0)
        has_holiday = bool(meta.get("has_holiday", 0))
        has_pre_holiday = bool(meta.get("has_pre_holiday", 0))
        spoilage_days = meta.get("spoilage_days", "?")

        summary_parts = [
            f"[Week {week} | {item} | {total_qty:.1f} {unit} sold",
            f"trend: {trend}",
            f"spoilage: {spoilage_days}d",
            f"revenue: ${revenue:.2f}",
        ]
        if has_holiday:
            summary_parts.append("PUBLIC HOLIDAY WEEK")
        if has_pre_holiday:
            summary_parts.append("PRE-HOLIDAY WEEK")
        lines.append(" | ".join(summary_parts) + "]")
        lines.append("")

    return "\n".join(lines)
