import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# VIC public holidays and Melbourne major events for 2026
# Each entry: (date_str, name, trade_type, foot_traffic_pct, order_adjustment_pct, notes)
# trade_type: "low" = the day itself (closed or low trade), "high" = day before (spike)
VIC_HOLIDAYS_2026: List[Tuple[str, str, str, int, int, str]] = [
    ("2026-01-01", "New Year's Day", "low", -60, -40, "Shop closed or minimal trade. Do not over-order perishables."),
    ("2026-01-02", "New Year's Day (observed)", "low", -30, -20, "Post-New Year slowdown. Reduce fresh items by 20%."),
    ("2026-01-26", "Australia Day", "low", -50, -35, "Public holiday. Many families BBQ at home - sausages and salads spike day before."),
    ("2026-01-25", "Australia Day eve", "high", +40, +30, "Pre-Australia Day spike. Increase salad items, tomatoes, corn 30-40%."),
    ("2026-03-09", "Labour Day", "low", -45, -30, "Public holiday. Long weekend away trips reduce foot traffic."),
    ("2026-03-08", "Labour Day eve", "high", +35, +25, "Pre-Labour Day. Increase stock for early weekend shoppers."),
    ("2026-04-03", "Good Friday", "low", -70, -50, "Most retailers closed. Minimal perishable orders needed."),
    ("2026-04-02", "Maundy Thursday (Good Friday eve)", "high", +55, +40, "Biggest pre-holiday spike of the year. Order 40-50% more across all categories."),
    ("2026-04-04", "Easter Saturday", "high", +45, +35, "Easter Saturday is high trade - families buying for Easter Sunday lunch."),
    ("2026-04-05", "Easter Sunday", "low", -30, -20, "Moderate reduction. Some retailers trade limited hours."),
    ("2026-04-06", "Easter Monday", "low", -55, -35, "Public holiday. Very low foot traffic. Minimal order needed."),
    ("2026-04-25", "ANZAC Day", "low", -65, -45, "Public holiday. Shops closed until midday. Reduce perishables significantly."),
    ("2026-04-24", "ANZAC Day eve", "high", +30, +20, "Moderate pre-holiday lift. Increase bread and deli items."),
    ("2026-06-08", "Queen's Birthday", "low", -50, -35, "Public holiday long weekend. Melbourne stays home or travels."),
    ("2026-06-07", "Queen's Birthday eve", "high", +38, +28, "Pre-Queen's Birthday. Increase root vegetables and hearty items for long weekend cooking."),
    ("2026-09-25", "AFL Grand Final Friday", "high", +60, +45, "AFL Grand Final Eve - huge spike. Party food demand surges. Increase dips, fruit platters, snack veg."),
    ("2026-09-26", "AFL Grand Final Saturday", "high", +70, +50, "AFL Grand Final day. Party food at peak. Increase fruit, veg platters, avocados for guac."),
    ("2026-11-03", "Melbourne Cup Day", "low", -40, -25, "Public holiday. CBD empties out. Suburban shops see light trade."),
    ("2026-11-02", "Melbourne Cup eve", "high", +30, +20, "Pre-Cup Day. Mild increase in party produce items."),
    ("2026-12-24", "Christmas Eve", "high", +80, +60, "Biggest single trading day of the year. Order 60-70% above normal across all items."),
    ("2026-12-25", "Christmas Day", "low", -85, -70, "Shop closed. Zero perishable order."),
    ("2026-12-26", "Boxing Day", "low", -45, -30, "Boxing Day sales draw foot traffic but mostly non-food retail. Reduce perishables."),
    ("2026-12-31", "New Year's Eve", "high", +50, +40, "NYE party shopping. Increase fruit platters, berries, champagne accompaniments."),
]

_HOLIDAY_LOOKUP: Dict[str, Tuple[str, str, str, int, int, str]] = {
    entry[0]: entry for entry in VIC_HOLIDAYS_2026
}


def _parse_date_input(date_input: str) -> Optional[date]:
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%B %d %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_input.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _format_holiday_entry(entry: Tuple[str, str, str, int, int, str]) -> str:
    date_str, name, trade_type, traffic_pct, order_adj, notes = entry
    traffic_label = f"{traffic_pct:+d}% vs normal"
    order_label = f"{order_adj:+d}%"
    trade_label = "LOW TRADE DAY" if trade_type == "low" else "HIGH TRADE DAY"
    return (
        f"  Date: {date_str}\n"
        f"  Event: {name} [{trade_label}]\n"
        f"  Foot traffic: {traffic_label}\n"
        f"  Order adjustment: {order_label}\n"
        f"  Notes: {notes}"
    )


def holiday_checker_tool(date_input: str) -> str:
    logger.info("holiday_checker_tool called with input: %s", date_input)

    check_range: List[date] = []

    if date_input.strip().lower() in ("next 7 days", "next7days", "next_7_days"):
        today = date.today()
        check_range = [today + timedelta(days=i) for i in range(8)]
    else:
        parsed = _parse_date_input(date_input)
        if parsed is None:
            return (
                f"Could not parse date input: '{date_input}'. "
                "Use YYYY-MM-DD format or 'next 7 days'."
            )
        # Check the date itself plus 3 days before and 3 days after for context
        check_range = [parsed + timedelta(days=i) for i in range(-3, 4)]

    found_entries: List[Tuple[str, Tuple]] = []
    for d in check_range:
        d_str = d.strftime("%Y-%m-%d")
        if d_str in _HOLIDAY_LOOKUP:
            found_entries.append((d_str, _HOLIDAY_LOOKUP[d_str]))

    lines = ["=== VIC Holiday and Events Check ===\n"]

    if not found_entries:
        date_desc = date_input if date_input.lower() not in ("next 7 days",) else "the next 7 days"
        lines.append(f"No public holidays or major events found around {date_desc}.")
        lines.append("Normal ordering rules apply. No adjustment needed.")
        return "\n".join(lines)

    lines.append(f"Found {len(found_entries)} relevant event(s):\n")
    for _, entry in found_entries:
        lines.append(_format_holiday_entry(entry))
        lines.append("")

    # Provide overall recommendation
    has_low = any(e[1][2] == "low" for e in found_entries)
    has_high = any(e[1][2] == "high" for e in found_entries)
    max_order_adj = max(e[1][4] for e in found_entries)
    min_order_adj = min(e[1][4] for e in found_entries)

    lines.append("--- Overall Recommendation ---")
    if has_high and has_low:
        lines.append(
            f"Mixed period: spike day(s) require up to {max_order_adj:+d}% more stock, "
            f"followed by low-trade day(s) at {min_order_adj:+d}%. "
            "Order early for the spike, hold back for the low-trade day."
        )
    elif has_high:
        lines.append(
            f"High-demand period ahead. Increase order by up to {max_order_adj:+d}%. "
            "Focus on high-velocity items: avocados, tomatoes, strawberries, broccoli."
        )
    else:
        lines.append(
            f"Low-trade period ahead. Reduce order by {abs(min_order_adj)}%. "
            "Prioritise long-shelf-life items. Avoid ordering highly perishable items (3-day shelf)."
        )

    return "\n".join(lines)
