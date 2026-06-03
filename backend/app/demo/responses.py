import time
from typing import Any, Dict


def json_safe(text: str) -> str:
    return text.replace('"', "'")


# Pre-written demo responses for demo mode.
# Each key matches one of the six demo queries exactly.
# Each value has: trace (list of AgentTraceStep dicts), tokens (response string), order (dict or None)

DEMO_RESPONSES: Dict[str, Dict[str, Any]] = {
    "what should i order this monday": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "weekly order recommendation Monday produce shop",
                "output": (
                    "Retrieved 4 records. Week 12 data shows strong Mon-Tue recovery after "
                    "Queen's Birthday weekend. Avocados and tomatoes performing above 8-week "
                    "average. Spinach trending +18% over last 3 weeks. Strawberries declining."
                ),
                "timestamp": time.time(),
            },
            {
                "tool_name": "holiday_checker",
                "input": "next 7 days",
                "output": (
                    "No public holidays this week. Normal trading week. "
                    "No event-driven demand adjustments required."
                ),
                "timestamp": time.time() + 0.3,
            },
            {
                "tool_name": "order_generator",
                "input": json_safe(
                    "Monday order, normal week, avocados trending up, strawberries declining"
                ),
                "output": (
                    "Generated order recommendation: 13 items. "
                    "Total estimated cost $1,847 AUD. Revenue $4,612 AUD. "
                    "High confidence on root vegetables and avocados. "
                    "Low confidence on stone fruit due to end-of-season volatility."
                ),
                "timestamp": time.time() + 0.6,
            },
        ],
        "tokens": (
            "Right, Monday order for a standard week. Here's what I'm seeing from the last 12 weeks of data.\n\n"
            "**Avocados** are your lead item this week - they've been running 15-20% above the 8-week average "
            "and the trend is still upward. Order 320 each. At $1.50 retail you'll move them easily.\n\n"
            "**Tomatoes** stay consistent - they're your highest-revenue vegetable week in, week out. "
            "Order 180kg. Don't go below this or you'll stock out by Wednesday afternoon.\n\n"
            "**Spinach** has been on a 3-week upward run, probably the cooler weather pushing demand. "
            "Bump it to 120 bunches, up from your usual 95.\n\n"
            "**Strawberries** - I'd pull back here. Trend has been declining for 4 weeks and we're coming "
            "into the colder months. Order 80 punnets, not 120. You'll sell them but the velocity isn't there "
            "to justify a full order.\n\n"
            "**Potatoes, carrots, onions** - order as normal. These are stable every week and have long "
            "shelf life so the downside risk is low.\n\n"
            "See the order table below for full quantities, costs, and confidence ratings. "
            "Get this in before Sunday 6pm."
        ),
        "order": {
            "items": [
                {
                    "item": "Avocados",
                    "quantity": 320.0,
                    "unit": "each",
                    "vs_normal_pct": 18.0,
                    "reasoning": "3-week upward trend, strong weekday velocity",
                    "confidence": "High",
                    "estimated_cost_aud": 256.0,
                    "estimated_revenue_aud": 480.0,
                },
                {
                    "item": "Tomatoes",
                    "quantity": 180.0,
                    "unit": "kg",
                    "vs_normal_pct": 5.0,
                    "reasoning": "Consistent performer, highest revenue vegetable",
                    "confidence": "High",
                    "estimated_cost_aud": 396.0,
                    "estimated_revenue_aud": 898.2,
                },
                {
                    "item": "Spinach",
                    "quantity": 120.0,
                    "unit": "bunch",
                    "vs_normal_pct": 26.0,
                    "reasoning": "Rising trend for 3 weeks, cooler weather driving demand",
                    "confidence": "Medium",
                    "estimated_cost_aud": 144.0,
                    "estimated_revenue_aud": 358.8,
                },
                {
                    "item": "Bananas",
                    "quantity": 200.0,
                    "unit": "kg",
                    "vs_normal_pct": 0.0,
                    "reasoning": "Stable demand, order as normal",
                    "confidence": "High",
                    "estimated_cost_aud": 240.0,
                    "estimated_revenue_aud": 598.0,
                },
                {
                    "item": "Potatoes",
                    "quantity": 250.0,
                    "unit": "kg",
                    "vs_normal_pct": 0.0,
                    "reasoning": "Stable, long shelf life, safe to order at normal levels",
                    "confidence": "High",
                    "estimated_cost_aud": 150.0,
                    "estimated_revenue_aud": 372.5,
                },
                {
                    "item": "Carrots",
                    "quantity": 180.0,
                    "unit": "kg",
                    "vs_normal_pct": 5.0,
                    "reasoning": "Slight upward trend, order marginally above normal",
                    "confidence": "High",
                    "estimated_cost_aud": 90.0,
                    "estimated_revenue_aud": 232.2,
                },
                {
                    "item": "Brown Onions",
                    "quantity": 160.0,
                    "unit": "kg",
                    "vs_normal_pct": 0.0,
                    "reasoning": "Stable, 30-day shelf life, no adjustment needed",
                    "confidence": "High",
                    "estimated_cost_aud": 88.0,
                    "estimated_revenue_aud": 238.4,
                },
                {
                    "item": "Broccoli",
                    "quantity": 180.0,
                    "unit": "each",
                    "vs_normal_pct": 10.0,
                    "reasoning": "Rising trend, cooler weather increasing demand",
                    "confidence": "Medium",
                    "estimated_cost_aud": 198.0,
                    "estimated_revenue_aud": 448.2,
                },
                {
                    "item": "Strawberries",
                    "quantity": 80.0,
                    "unit": "punnet",
                    "vs_normal_pct": -33.0,
                    "reasoning": "Declining 4 weeks, seasonal drop-off into winter",
                    "confidence": "High",
                    "estimated_cost_aud": 200.0,
                    "estimated_revenue_aud": 319.2,
                },
                {
                    "item": "Lemons",
                    "quantity": 200.0,
                    "unit": "each",
                    "vs_normal_pct": 8.0,
                    "reasoning": "Rising, good value and long shelf life",
                    "confidence": "Medium",
                    "estimated_cost_aud": 80.0,
                    "estimated_revenue_aud": 198.0,
                },
                {
                    "item": "Sweet Potato",
                    "quantity": 140.0,
                    "unit": "kg",
                    "vs_normal_pct": 5.0,
                    "reasoning": "Slight seasonal uptick, stable performer",
                    "confidence": "Medium",
                    "estimated_cost_aud": 196.0,
                    "estimated_revenue_aud": 418.6,
                },
                {
                    "item": "Zucchini",
                    "quantity": 90.0,
                    "unit": "kg",
                    "vs_normal_pct": -5.0,
                    "reasoning": "Slightly softer, trim back marginally",
                    "confidence": "Medium",
                    "estimated_cost_aud": 162.0,
                    "estimated_revenue_aud": 314.1,
                },
                {
                    "item": "Mangoes",
                    "quantity": 40.0,
                    "unit": "each",
                    "vs_normal_pct": -65.0,
                    "reasoning": "End of season, sell through last of stock only",
                    "confidence": "Low",
                    "estimated_cost_aud": 60.0,
                    "estimated_revenue_aud": 100.0,
                },
            ],
            "total_cost_aud": 2060.0,
            "total_revenue_aud": 4776.2,
            "order_by": "Sunday 6pm",
            "confidence": "High",
            "notes": (
                "Mangoes at end of season - order minimum and mark price down if unsold by Wednesday. "
                "Peaches and nectarines not included - season over, do not order."
            ),
        },
    },
    "are strawberries still worth ordering in june": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "strawberries June seasonal demand trend",
                "output": (
                    "Retrieved 4 records for strawberries weeks 8-12. "
                    "Weeks 8-9: 480-520 punnets/week. Week 10: 380 punnets. "
                    "Week 11: 290 punnets. Week 12: 210 punnets. "
                    "Consistent declining trend. Spoilage risk increasing."
                ),
                "timestamp": time.time(),
            },
            {
                "tool_name": "spoilage_scorer",
                "input": "Strawberries",
                "output": (
                    "Spoilage risk: HIGH. Spoilage window 3 days. Trend: declining. "
                    "Current daily avg 30 punnets vs 74 punnets 4 weeks ago. "
                    "Recommendation: reduce order to 50-60 punnets, place prominently, "
                    "consider 2-for-1 on older stock."
                ),
                "timestamp": time.time() + 0.3,
            },
        ],
        "tokens": (
            "Short answer: yes, but with a much smaller order and a clear markdown plan.\n\n"
            "Looking at the data, strawberries have dropped from **520 punnets per week** in late April "
            "to about **210 punnets** by mid-May. That's a 60% decline in 5 weeks. "
            "This is completely normal - Queensland and Victorian strawberry season winds down in June "
            "and we shift to imported (mostly SA greenhouse) stock which is more expensive and less vibrant.\n\n"
            "**What to order in June:** 50-60 punnets per week maximum. "
            "Display them near the front, ideally eye level. "
            "If you haven't sold through by Thursday, drop to 2 for $6 "
            "(still above your $2.50 cost price).\n\n"
            "**Why still order at all?** Loyal customers expect to see them. "
            "A bare strawberry shelf in June looks like poor management even if demand is low. "
            "50 punnets is manageable and keeps the display looking full.\n\n"
            "**What I'd watch:** if weekly sales drop below 40 punnets, cut to 30 or drop the line "
            "entirely until July when tunnel-grown Victorian stock picks back up.\n\n"
            "Spoilage risk is HIGH with a 3-day shelf. Every punnet unsold by day 3 is a dead loss. "
            "Don't let sentiment override the data here."
        ),
        "order": None,
    },
    "queens birthday is next week how do i adjust": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "Queen's Birthday long weekend ordering adjustment",
                "output": (
                    "Retrieved 4 records. Previous Queen's Birthday week showed -45% foot traffic "
                    "on the Monday, +35% on the Saturday before. "
                    "Root vegetables and hearty items outperform on pre-long-weekend days. "
                    "Perishables with 3-day shelf suffered significant waste."
                ),
                "timestamp": time.time(),
            },
            {
                "tool_name": "holiday_checker",
                "input": "2026-06-08",
                "output": (
                    "Queen's Birthday: 8 June 2026. LOW TRADE DAY (-50% foot traffic). "
                    "Pre-holiday eve (7 June): HIGH TRADE DAY (+38%). "
                    "Reduce overall order by 35%. Focus on long shelf-life items for the weekend."
                ),
                "timestamp": time.time() + 0.3,
            },
            {
                "tool_name": "order_generator",
                "input": json_safe(
                    "Queen's Birthday long weekend adjustment, low trade Monday, spike Saturday"
                ),
                "output": (
                    "Generated Queen's Birthday adjusted order: 11 items. "
                    "Overall -32% vs normal week. "
                    "Eliminated 3-day perishables. Increased root vegetables for weekend cooking."
                ),
                "timestamp": time.time() + 0.6,
            },
        ],
        "tokens": (
            "Queen's Birthday long weekend - this one catches people out every year.\n\n"
            "**The pattern:** Saturday before is a good trading day (+35-40% foot traffic as people "
            "stock up for the long weekend). Sunday is normal. Monday is dead - you're looking at "
            "-50% or more. A lot of families go away or just stay home and don't shop.\n\n"
            "**What this means for your order:**\n\n"
            "Reduce your total order by about 30-35% versus a normal week. "
            "The key risk is that anything with a 3-day shelf you order on Monday won't sell through "
            "by Thursday if foot traffic is that low.\n\n"
            "**Increase:** potatoes, sweet potato, carrots, onions, broccoli. "
            "People cooking at home over the long weekend want hearty stuff. "
            "These also have long shelf life so the risk is low.\n\n"
            "**Decrease significantly:** strawberries (3-day shelf), spinach (3-day shelf), "
            "fresh herbs. Reduce these by 40-50%.\n\n"
            "**Normal:** avocados, tomatoes, bananas - these sell across the week regardless.\n\n"
            "**Timing:** if you can, place two smaller orders - one for the Saturday spike, "
            "one lighter top-up for the following week. Beats one big order that sits over the holiday.\n\n"
            "See the adjusted order table below."
        ),
        "order": {
            "items": [
                {
                    "item": "Potatoes",
                    "quantity": 280.0,
                    "unit": "kg",
                    "vs_normal_pct": 12.0,
                    "reasoning": "Long weekend home cooking, 21-day shelf",
                    "confidence": "High",
                    "estimated_cost_aud": 168.0,
                    "estimated_revenue_aud": 417.2,
                },
                {
                    "item": "Sweet Potato",
                    "quantity": 160.0,
                    "unit": "kg",
                    "vs_normal_pct": 14.0,
                    "reasoning": "Winter roasting staple, long weekend demand",
                    "confidence": "High",
                    "estimated_cost_aud": 224.0,
                    "estimated_revenue_aud": 478.4,
                },
                {
                    "item": "Carrots",
                    "quantity": 190.0,
                    "unit": "kg",
                    "vs_normal_pct": 8.0,
                    "reasoning": "Long shelf life, winter stew ingredient",
                    "confidence": "High",
                    "estimated_cost_aud": 95.0,
                    "estimated_revenue_aud": 245.1,
                },
                {
                    "item": "Brown Onions",
                    "quantity": 170.0,
                    "unit": "kg",
                    "vs_normal_pct": 6.0,
                    "reasoning": "30-day shelf, core winter cooking item",
                    "confidence": "High",
                    "estimated_cost_aud": 93.5,
                    "estimated_revenue_aud": 253.3,
                },
                {
                    "item": "Broccoli",
                    "quantity": 160.0,
                    "unit": "each",
                    "vs_normal_pct": 0.0,
                    "reasoning": "Stable, winter vegetable staple",
                    "confidence": "Medium",
                    "estimated_cost_aud": 176.0,
                    "estimated_revenue_aud": 398.4,
                },
                {
                    "item": "Avocados",
                    "quantity": 260.0,
                    "unit": "each",
                    "vs_normal_pct": -8.0,
                    "reasoning": "Slight reduction, fewer Saturday brunchers over long w/e",
                    "confidence": "Medium",
                    "estimated_cost_aud": 208.0,
                    "estimated_revenue_aud": 390.0,
                },
                {
                    "item": "Tomatoes",
                    "quantity": 140.0,
                    "unit": "kg",
                    "vs_normal_pct": -22.0,
                    "reasoning": "Reduce due to lower mid-week traffic",
                    "confidence": "High",
                    "estimated_cost_aud": 308.0,
                    "estimated_revenue_aud": 698.6,
                },
                {
                    "item": "Bananas",
                    "quantity": 180.0,
                    "unit": "kg",
                    "vs_normal_pct": -10.0,
                    "reasoning": "Slight reduction for holiday week",
                    "confidence": "Medium",
                    "estimated_cost_aud": 216.0,
                    "estimated_revenue_aud": 538.2,
                },
                {
                    "item": "Spinach",
                    "quantity": 60.0,
                    "unit": "bunch",
                    "vs_normal_pct": -50.0,
                    "reasoning": "3-day shelf, cut hard for low-trade period",
                    "confidence": "High",
                    "estimated_cost_aud": 72.0,
                    "estimated_revenue_aud": 179.4,
                },
                {
                    "item": "Strawberries",
                    "quantity": 40.0,
                    "unit": "punnet",
                    "vs_normal_pct": -50.0,
                    "reasoning": "3-day shelf, declining season, holiday week risk",
                    "confidence": "High",
                    "estimated_cost_aud": 100.0,
                    "estimated_revenue_aud": 159.6,
                },
                {
                    "item": "Lemons",
                    "quantity": 180.0,
                    "unit": "each",
                    "vs_normal_pct": 0.0,
                    "reasoning": "14-day shelf, safe to order at normal level",
                    "confidence": "High",
                    "estimated_cost_aud": 72.0,
                    "estimated_revenue_aud": 178.2,
                },
            ],
            "total_cost_aud": 1732.5,
            "total_revenue_aud": 3936.4,
            "order_by": "Saturday 4pm (before the long weekend)",
            "confidence": "High",
            "notes": (
                "Peaches, nectarines, zucchini not included - reduce these to minimum if you carry them. "
                "Do NOT order fresh herbs this week - zero chance of selling through over the public holiday. "
                "Consider placing a smaller top-up order Tuesday morning for mid-week restocking."
            ),
        },
    },
    "we have leftover strawberries from friday what do we do": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "strawberries leftover weekend markdown strategy",
                "output": (
                    "Retrieved 3 records. Strawberry weekend velocity typically drops 40% "
                    "vs weekday average. Sunday is weakest day for strawberries - "
                    "customers buy fresh weekly shops Monday-Wednesday. "
                    "Friday-Saturday leftover strawberries with 3-day shelf = critical risk by Sunday."
                ),
                "timestamp": time.time(),
            },
            {
                "tool_name": "spoilage_scorer",
                "input": "Strawberries",
                "output": (
                    "Spoilage risk: CRITICAL. 3-day shelf. "
                    "If purchased/delivered Friday, sell-by is Sunday/Monday. "
                    "Current declining trend. "
                    "Action: immediate markdown or bundling required. "
                    "Do not carry unsold stock into next week."
                ),
                "timestamp": time.time() + 0.3,
            },
        ],
        "tokens": (
            "Okay, Friday leftover strawberries - you've got a tight window. "
            "With a 3-day shelf, your deadline is Sunday at absolute latest, Monday morning at a push if "
            "they were in good condition when they arrived.\n\n"
            "**Do this now:**\n\n"
            "1. **Mark them down immediately.** If they're $3.99 each, go to $2.99 today, "
            "then 2 for $5 tomorrow. At $2.50 wholesale cost, 2 for $5 still breaks even. "
            "Every punnet sold at cost is better than a full write-off.\n\n"
            "2. **Move them to the front of the store.** End cap, front-of-store bin, eye level. "
            "Don't leave them in the regular fridge position.\n\n"
            "3. **Bundle with cream or yoghurt if you carry it.** "
            "Strawberries plus cream is a very easy add-on and moves stock fast.\n\n"
            "4. **Post on socials if you have it.** 'Weekend special - strawberries 2 for $5 today only.' "
            "Takes 2 minutes and moves units.\n\n"
            "**For next week's order:** if you're regularly seeing Friday leftovers, "
            "your order size is wrong for the back half of the week. "
            "Cut your strawberry order by 15-20% and order twice a week if your supplier allows it. "
            "Strawberries should not be sitting 3 days - that's a buying pattern problem, not just bad luck.\n\n"
            "**How many do you have left?** If it's 20 or fewer punnets, markdown and you'll clear them. "
            "If it's 50+, call your supplier and ask about returns or credit - most Melbourne wholesalers "
            "will work with you on perishables if you ask before they're gone."
        ),
        "order": None,
    },
    "should i order mangoes this week": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "mangoes seasonal demand trend June ordering",
                "output": (
                    "Retrieved 4 records for mangoes. Peak sales weeks 1-4 (Jan-Feb): "
                    "820-950 each per week. Week 8: 420 each. Week 10: 240 each. "
                    "Week 12: 120 each. Sharp seasonal decline. "
                    "Spoilage days 4. Price has risen as season ends."
                ),
                "timestamp": time.time(),
            },
            {
                "tool_name": "spoilage_scorer",
                "input": "Mangoes",
                "output": (
                    "Spoilage risk: HIGH. 4-day shelf. Declining trend (-65% vs peak). "
                    "Current avg 17 each/day vs 130+ each/day at season peak. "
                    "Recommendation: order 30-40 each maximum. Display prominently. "
                    "If not cleared in 3 days, mark down immediately."
                ),
                "timestamp": time.time() + 0.3,
            },
        ],
        "tokens": (
            "Mangoes in June - this is basically an end-of-season call and the answer is: "
            "a small token order only, or skip entirely.\n\n"
            "**The season story:** Melbourne mango season runs roughly October to April. "
            "At peak (January-February), a well-run shop moves 120-150 mangoes per day. "
            "By May that's dropped to 15-20 per day. By June you're lucky to move 10. "
            "The fruit is also coming from Northern Territory now (Kensington Pride late season) "
            "and quality is inconsistent - you'll get a tray with 6 good and 6 on the turn.\n\n"
            "**What the data says:** your shop peaked at 940 mangoes per week in week 2 (mid-January). "
            "Week 12 was 120. That's an 87% decline. The trend is still falling.\n\n"
            "**My recommendation:** Order 30-40 this week if you want to keep the display going. "
            "Some customers still ask for them and it avoids a bare section. "
            "At $2.50 wholesale and $2.99-$3.49 retail you have minimal margin left - "
            "this is more about display than profit at this point.\n\n"
            "**Do NOT order a full case (usually 5-8kg, ~20-30 fruit) expecting normal sales.** "
            "Your velocity at 10-15 per day means a standard case of 30 takes 2-3 days. "
            "With a 4-day shelf, that's tight.\n\n"
            "**Skip mangoes entirely if:** your supplier can't do partial cases, "
            "or if last week you had waste. Cut the line and replace with a seasonal alternative "
            "- persimmons or late-season feijoas are good June alternatives that move better.\n\n"
            "Mangoes will be back with the new season in October."
        ),
        "order": None,
    },
    "which items have been our best performers this month": {
        "trace": [
            {
                "tool_name": "sales_retriever",
                "input": "best performing items revenue quantity sold month",
                "output": (
                    "Retrieved top performing records. Avocados: $4,820 revenue across 4 weeks. "
                    "Tomatoes: $5,640 revenue, highest single-item revenue. "
                    "Bananas: $4,190 revenue, highest volume. "
                    "Broccoli: +18% trend over 4 weeks. "
                    "Spinach: +22% trend over 4 weeks. "
                    "Strawberries: -55% decline, lowest performer by trend."
                ),
                "timestamp": time.time(),
            },
        ],
        "tokens": (
            "Here's how the month has stacked up based on the last 4 weeks of data:\n\n"
            "**By Revenue (AUD):**\n"
            "1. **Tomatoes** - $5,640 total. Your anchor item. Consistent every week, "
            "high price point ($4.99/kg) and strong volume. Never had a bad week.\n"
            "2. **Avocados** - $4,820 total. Volume has been building - up 18% over the period. "
            "Best margin-to-space ratio in the shop.\n"
            "3. **Bananas** - $4,190 total. Volume leader but lower margin. "
            "Still essential - they're a reason people walk in.\n"
            "4. **Potatoes** - $3,840 total. Bread and butter. Low price, high volume.\n"
            "5. **Broccoli** - $3,210 total and rising. "
            "Trending +18% - this is your hot item right now.\n\n"
            "**By Growth Trend (last 4 weeks):**\n"
            "- Spinach: +22% - strongest grower. "
            "Classic winter trend, worth increasing stock.\n"
            "- Broccoli: +18% - follow the spinach story, same dynamic.\n"
            "- Lemons: +14% - people are making more hot drinks and cooking with citrus.\n"
            "- Avocados: +18% - strong and sustained, not just a one-week spike.\n\n"
            "**Underperformers to watch:**\n"
            "- Strawberries: -55% over 4 weeks. Seasonal, expected, but act on it.\n"
            "- Mangoes: -65% over 4 weeks. Cut your order now.\n"
            "- Peaches/Nectarines: off the boil, season is ending. "
            "Wind these down or drop them.\n\n"
            "**Bottom line:** lean into the winter vegetables (broccoli, spinach, "
            "sweet potato, root veg) and hold firm on avocados and tomatoes. "
            "Use the freed-up shelf space from stone fruit for "
            "citrus and leafy greens going into June."
        ),
        "order": None,
    },
}
