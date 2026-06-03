import json
import logging
from datetime import datetime
from typing import Any, Dict

from app.services.llm import get_llm_service
from app.models import OrderItem, OrderRecommendation


logger = logging.getLogger(__name__)

ORDER_SYSTEM_PROMPT = """You are an experienced Melbourne produce manager with 15 years at a high-volume fresh produce shop.
You generate precise ordering recommendations based on historical sales data, holiday context, and spoilage risk.

You must respond with valid JSON only, exactly matching this schema:
{
  "items": [
    {
      "item": "string",
      "quantity": number,
      "unit": "string",
      "vs_normal_pct": number (percentage vs typical week, e.g. +20 or -15),
      "reasoning": "string (one sentence)",
      "confidence": "High" | "Medium" | "Low",
      "estimated_cost_aud": number,
      "estimated_revenue_aud": number
    }
  ],
  "total_cost_aud": number,
  "total_revenue_aud": number,
  "order_by": "string (e.g. Sunday 6pm)",
  "confidence": "string",
  "notes": "string"
}

Be precise with quantities. Base your recommendations on the historical data provided.
Use realistic Melbourne wholesale prices: bananas ~$1.20/kg, strawberries ~$2.50/punnet, avocados ~$0.80/each,
tomatoes ~$2.20/kg, potatoes ~$0.60/kg, carrots ~$0.50/kg, onions ~$0.55/kg, spinach ~$1.20/bunch,
broccoli ~$1.10/each, mangoes ~$1.50/each, lemons ~$0.40/each, zucchini ~$1.80/kg.
Retail prices are approximately 2.5x wholesale.
Never include items that should be skipped due to spoilage risk - instead note them in the 'notes' field.
"""


def _build_order_prompt(
    retrieved_context: str,
    holiday_context: str,
    spoilage_context: str,
    user_query: str,
) -> str:
    now = datetime.now()
    date_line = (
        f"TODAY: {now.strftime('%A, %d %B %Y')} | "
        f"{now.strftime('%I:%M %p')} | "
        f"Melbourne, Victoria, Australia"
    )
    return f"""CURRENT DATE & TIME: {date_line}

User query: {user_query}

HISTORICAL SALES CONTEXT:
{retrieved_context}

HOLIDAY AND EVENTS CONTEXT:
{holiday_context}

SPOILAGE RISK CONTEXT:
{spoilage_context}

Based on all of the above, generate a complete order recommendation for a Melbourne produce shop.
Respond with valid JSON only, no markdown, no explanation."""


def _format_order_table(order: OrderRecommendation) -> str:
    header = f"{'Item':<18} {'Qty':>7} {'Unit':<8} {'vs Normal':>10} {'Conf':<8} Reasoning"
    separator = "-" * 90
    rows = [header, separator]

    for item in order.items:
        vs_str = f"{item.vs_normal_pct:+.0f}%"
        if item.vs_normal_pct > 0:
            vs_prefix = "+"
        elif item.vs_normal_pct < 0:
            vs_prefix = "-"
        else:
            vs_prefix = " "

        if abs(item.vs_normal_pct) < 1 and item.quantity == 0:
            qty_str = "SKIP"
            vs_str = "SKIP"
        else:
            qty_str = f"{item.quantity:.1f}"

        row = (
            f"{item.item:<18} {qty_str:>7} {item.unit:<8} "
            f"{vs_str:>10} {item.confidence:<8} {item.reasoning[:45]}"
        )
        rows.append(row)

    rows.append(separator)
    rows.append(
        f"{'TOTALS':<18} {'':>7} {'':8} {'':>10} {'':8} "
        f"Cost: ${order.total_cost_aud:.2f} | Revenue: ${order.total_revenue_aud:.2f}"
    )
    rows.append(f"\nOrder by: {order.order_by}")
    rows.append(f"Overall confidence: {order.confidence}")
    rows.append(f"Notes: {order.notes}")
    return "\n".join(rows)


def order_generator_tool(context_json: str) -> str:
    logger.info("order_generator_tool called")

    try:
        ctx: Dict[str, Any] = json.loads(context_json)
    except json.JSONDecodeError as exc:
        logger.error("order_generator_tool: invalid JSON input: %s", exc)
        return f"Error: invalid context JSON: {exc}"

    retrieved_context = ctx.get("retrieved_context", "No historical data available.")
    holiday_context = ctx.get("holiday_context", "No holiday context available.")
    spoilage_context = ctx.get("spoilage_context", "No spoilage data available.")
    user_query = ctx.get("user_query", "Generate an order recommendation.")

    prompt = _build_order_prompt(
        retrieved_context, holiday_context, spoilage_context, user_query
    )

    try:
        llm = get_llm_service()
        raw_response = llm.complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=ORDER_SYSTEM_PROMPT,
            max_tokens=2000,
        )
    except Exception as exc:
        logger.error("order_generator_tool LLM call failed: %s", exc)
        return f"Error generating order: {exc}"

    # Strip any accidental markdown fencing
    raw_response = raw_response.strip()
    if raw_response.startswith("```"):
        lines = raw_response.split("\n")
        raw_response = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    try:
        order_dict: Dict[str, Any] = json.loads(raw_response)
        items = [OrderItem(**item) for item in order_dict.get("items", [])]
        order = OrderRecommendation(
            items=items,
            total_cost_aud=float(order_dict.get("total_cost_aud", 0)),
            total_revenue_aud=float(order_dict.get("total_revenue_aud", 0)),
            order_by=order_dict.get("order_by", "Sunday 6pm"),
            confidence=order_dict.get("confidence", "Medium"),
            notes=order_dict.get("notes", ""),
        )
    except Exception as exc:
        logger.error("order_generator_tool failed to parse LLM response: %s | raw: %s", exc, raw_response[:200])
        return f"Error parsing order recommendation: {exc}\n\nRaw LLM output:\n{raw_response[:500]}"

    table = _format_order_table(order)
    order_json = order.model_dump_json()

    result = f"ORDER_JSON:{order_json}\n\nORDER_TABLE:\n{table}"
    logger.info("order_generator_tool completed successfully: %d items", len(order.items))
    return result
