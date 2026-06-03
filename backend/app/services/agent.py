import json
import logging
import time
import uuid
from datetime import datetime
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.models import SSEEvent
from app.services.llm import get_llm_service
from app.tools.sales_retriever import sales_retriever_tool
from app.tools.spoilage_scorer import spoilage_scorer_tool
from app.tools.holiday_checker import holiday_checker_tool
from app.tools.order_generator import order_generator_tool
from app.tools.demand_forecaster import demand_forecaster_tool


logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MarketMate, an AI ordering assistant for a Melbourne fresh produce retailer.
You have deep knowledge of produce seasonality, Melbourne shopping patterns, and practical retail operations.
You speak like an experienced produce manager - direct, practical, and confident - not like a corporate AI assistant.
Use the retrieved sales data, holiday context, and spoilage information to give specific, actionable advice.
Never give vague or hedged answers when data is available. Reference specific numbers from the context.
When an order table has been generated, refer to it as 'the order table below' and do not repeat all quantities in prose.
Use Australian English. Keep responses focused and under 400 words unless a full order table is needed.
CRITICAL DATE RULES:
- The current date and time is always provided at the top of each message as CURRENT DATE & TIME.
- Always use this exact date when referencing today, tomorrow, or specific days.
- When the user says 'next monday' calculate it precisely from the current date.
- Never guess or assume the date - it is always explicitly provided.
- Always state the exact date (e.g. Thursday 4 June 2026) not just the day name when discussing ordering windows.
- No emojis in responses."""


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    retrieved_context: str
    holiday_context: str
    spoilage_context: str
    forecast_context: str
    order_recommendation: Optional[Dict[str, Any]]
    agent_trace: List[Dict[str, Any]]
    final_response: str
    session_id: str
    should_call_holiday: bool
    should_call_spoilage: bool
    should_call_order: bool
    should_call_forecast: bool


def _make_trace_entry(tool_name: str, input_text: str, output_text: str) -> Dict[str, Any]:
    return {
        "tool_name": tool_name,
        "input": input_text,
        "output": output_text[:300],
        "timestamp": time.time(),
    }


def _should_call_holiday(query: str) -> bool:
    keywords = [
        "holiday", "public holiday", "weekend", "long weekend", "monday",
        "event", "date", "christmas", "easter", "queens", "anzac", "cup",
        "grand final", "afl", "new year", "australia day", "labour day",
        "next week", "this week", "jan", "feb", "mar", "apr", "jun", "jul",
        "aug", "sep", "oct", "nov", "dec",
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)


def _should_call_spoilage(query: str) -> bool:
    keywords = [
        "leftover", "left over", "waste", "spoil", "spoilage", "old stock",
        "unsold", "still have", "excess", "overstock", "going off",
        "mark down", "markdown", "clearance", "friday", "weekend leftover",
        "what do i do with", "got some",
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)


def _should_call_order(query: str) -> bool:
    keywords = [
        "order", "how much", "how many", "what to buy", "what should i",
        "recommend", "recommendation", "stock", "buy", "purchase",
        "this week", "next week", "monday", "adjust",
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)


def _should_call_forecast(query: str) -> bool:
    keywords = [
        "forecast", "predict", "prediction", "trend", "next week", "demand",
        "expect", "projection", "will sell", "how many will", "performance",
        "best sellers", "top items", "growing", "declining", "rising",
        "season", "pattern", "historical",
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)


def _extract_item_for_spoilage(query: str) -> str:
    items = [
        "bananas", "strawberries", "avocados", "tomatoes", "potatoes",
        "carrots", "brown onions", "spinach", "broccoli", "mangoes",
        "peaches", "nectarines", "lemons", "zucchini", "sweet potato",
    ]
    query_lower = query.lower()
    for item in items:
        if item in query_lower:
            return item.title()
    return "Strawberries"


def query_router_node(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("query_router_node: routing query '%s'", query[:80])
    return {
        **state,
        "should_call_holiday": _should_call_holiday(query),
        "should_call_spoilage": _should_call_spoilage(query),
        "should_call_order": _should_call_order(query),
        "should_call_forecast": _should_call_forecast(query),
        "retrieved_context": "",
        "holiday_context": "",
        "spoilage_context": "",
        "forecast_context": "",
        "order_recommendation": None,
        "agent_trace": state.get("agent_trace", []),
    }


def sales_retriever_node(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("sales_retriever_node: retrieving for query '%s'", query[:80])
    result = sales_retriever_tool(query)
    trace_entry = _make_trace_entry("sales_retriever", query[:150], result[:300])
    return {
        **state,
        "retrieved_context": result,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }


def holiday_checker_node(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("holiday_checker_node: checking holidays for '%s'", query[:80])
    result = holiday_checker_tool("next 7 days")
    trace_entry = _make_trace_entry("holiday_checker", "next 7 days", result[:300])
    return {
        **state,
        "holiday_context": result,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }


def spoilage_scorer_node(state: AgentState) -> AgentState:
    query = state["query"]
    item = _extract_item_for_spoilage(query)
    logger.info("spoilage_scorer_node: scoring '%s'", item)
    result = spoilage_scorer_tool(item)
    trace_entry = _make_trace_entry("spoilage_scorer", item, result[:300])
    return {
        **state,
        "spoilage_context": result,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }


def demand_forecaster_node(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info("demand_forecaster_node: forecasting")
    items = [
        "Bananas", "Avocados", "Tomatoes", "Strawberries", "Spinach",
        "Broccoli", "Potatoes", "Carrots", "Brown Onions", "Mangoes",
    ]
    mentioned = [i for i in items if i.lower() in query.lower()]
    target_items = ",".join(mentioned) if mentioned else ",".join(items[:6])
    result = demand_forecaster_tool(target_items)
    trace_entry = _make_trace_entry("demand_forecaster", target_items, result[:300])
    return {
        **state,
        "forecast_context": result,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }


def order_generator_node(state: AgentState) -> AgentState:
    logger.info("order_generator_node: generating order")
    context = {
        "retrieved_context": state.get("retrieved_context", ""),
        "holiday_context": state.get("holiday_context", ""),
        "spoilage_context": state.get("spoilage_context", ""),
        "user_query": state["query"],
    }
    result = order_generator_tool(json.dumps(context))

    order_dict = None
    if "ORDER_JSON:" in result:
        try:
            json_part = result.split("ORDER_JSON:")[1].split("\n\nORDER_TABLE:")[0].strip()
            order_dict = json.loads(json_part)
        except Exception as exc:
            logger.warning("order_generator_node: failed to parse order JSON: %s", exc)

    trace_entry = _make_trace_entry("order_generator", state["query"][:150], result[:300])
    return {
        **state,
        "order_recommendation": order_dict,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }


def response_synthesiser_node(state: AgentState) -> AgentState:
    logger.info("response_synthesiser_node: generating final response")
    query = state["query"]
    retrieved = state.get("retrieved_context", "")
    holiday = state.get("holiday_context", "")
    spoilage = state.get("spoilage_context", "")
    forecast = state.get("forecast_context", "")
    order = state.get("order_recommendation")
    history = state.get("messages", [])

    now = datetime.now()
    date_ctx = (
        f"TODAY: {now.strftime('%A, %d %B %Y')} | "
        f"Time: {now.strftime('%I:%M %p')} | "
        f"Week {now.isocalendar()[1]} of {now.year} | "
        f"Location: Melbourne, Victoria, Australia"
    )

    context_parts = [
        f"CURRENT DATE & TIME: {date_ctx}",
        f"User query: {query}",
    ]
    if retrieved:
        context_parts.append(f"\nHISTORICAL SALES DATA:\n{retrieved[:800]}")
    if forecast:
        context_parts.append(f"\nDATA-DRIVEN DEMAND FORECAST (statistical model):\n{forecast[:600]}")
    if holiday:
        context_parts.append(f"\nHOLIDAY/EVENT CONTEXT:\n{holiday[:400]}")
    if spoilage:
        context_parts.append(f"\nSPOILAGE RISK:\n{spoilage[:400]}")
    if order:
        context_parts.append(
            "\nAn order table has been generated and will be shown to the user below your response. "
            "Reference it as 'the order table below' - do not repeat all quantities in prose."
        )

    messages: List[Dict[str, str]] = []
    for msg in history:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role = "user" if msg.type == "human" else "assistant"
            messages.append({"role": role, "content": str(msg.content)})

    messages.append({"role": "user", "content": "\n".join(context_parts)})

    try:
        llm = get_llm_service()
        response = llm.complete(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=800,
        )
    except Exception as exc:
        logger.error("response_synthesiser_node LLM error: %s", exc, exc_info=True)
        response = (
            "I ran into an issue generating a response. "
            "The sales data was retrieved but the language model is unavailable. "
            "Please try again or check your API key."
        )

    return {**state, "final_response": response}


def _route_after_query_router(state: AgentState) -> str:
    return "sales_retriever"


def _route_after_sales_retriever(state: AgentState) -> str:
    if state.get("should_call_forecast"):
        return "demand_forecaster"
    if state.get("should_call_holiday"):
        return "holiday_checker"
    if state.get("should_call_spoilage"):
        return "spoilage_scorer"
    if state.get("should_call_order"):
        return "order_generator"
    return "response_synthesiser"


def _route_after_demand_forecaster(state: AgentState) -> str:
    if state.get("should_call_holiday"):
        return "holiday_checker"
    if state.get("should_call_spoilage"):
        return "spoilage_scorer"
    if state.get("should_call_order"):
        return "order_generator"
    return "response_synthesiser"


def _route_after_holiday_checker(state: AgentState) -> str:
    if state.get("should_call_spoilage"):
        return "spoilage_scorer"
    if state.get("should_call_order"):
        return "order_generator"
    return "response_synthesiser"


def _route_after_spoilage_scorer(state: AgentState) -> str:
    if state.get("should_call_order"):
        return "order_generator"
    return "response_synthesiser"


def _build_graph() -> Any:
    graph = StateGraph(AgentState)

    graph.add_node("query_router", query_router_node)
    graph.add_node("sales_retriever", sales_retriever_node)
    graph.add_node("demand_forecaster", demand_forecaster_node)
    graph.add_node("holiday_checker", holiday_checker_node)
    graph.add_node("spoilage_scorer", spoilage_scorer_node)
    graph.add_node("order_generator", order_generator_node)
    graph.add_node("response_synthesiser", response_synthesiser_node)

    graph.set_entry_point("query_router")

    graph.add_conditional_edges(
        "query_router",
        _route_after_query_router,
        {"sales_retriever": "sales_retriever"},
    )
    graph.add_conditional_edges(
        "sales_retriever",
        _route_after_sales_retriever,
        {
            "demand_forecaster": "demand_forecaster",
            "holiday_checker": "holiday_checker",
            "spoilage_scorer": "spoilage_scorer",
            "order_generator": "order_generator",
            "response_synthesiser": "response_synthesiser",
        },
    )
    graph.add_conditional_edges(
        "holiday_checker",
        _route_after_holiday_checker,
        {
            "spoilage_scorer": "spoilage_scorer",
            "order_generator": "order_generator",
            "response_synthesiser": "response_synthesiser",
        },
    )
    graph.add_conditional_edges(
        "spoilage_scorer",
        _route_after_spoilage_scorer,
        {
            "order_generator": "order_generator",
            "response_synthesiser": "response_synthesiser",
        },
    )
    graph.add_conditional_edges(
        "demand_forecaster",
        _route_after_demand_forecaster,
        {
            "holiday_checker": "holiday_checker",
            "spoilage_scorer": "spoilage_scorer",
            "order_generator": "order_generator",
            "response_synthesiser": "response_synthesiser",
        },
    )
    graph.add_edge("order_generator", "response_synthesiser")
    graph.add_edge("response_synthesiser", END)

    return graph.compile()


_compiled_graph: Optional[Any] = None


def get_agent_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
        logger.info("LangGraph MarketMateAgent compiled with %d nodes", 7)
    return _compiled_graph


class MarketMateAgent:
    def __init__(self) -> None:
        self._graph = get_agent_graph()

    async def run(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        session_id: str,
    ) -> AsyncGenerator[SSEEvent, None]:
        logger.info("MarketMateAgent.run: session=%s query='%s'", session_id, query[:80])

        from langchain_core.messages import HumanMessage, AIMessage

        messages: List[BaseMessage] = []
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=query))

        initial_state: AgentState = {
            "messages": messages,
            "query": query,
            "retrieved_context": "",
            "holiday_context": "",
            "spoilage_context": "",
            "order_recommendation": None,
            "agent_trace": [],
            "final_response": "",
            "session_id": session_id,
            "should_call_holiday": False,
            "should_call_spoilage": False,
            "should_call_order": False,
        }

        emitted_trace_count = 0

        try:
            async for step_output in self._graph.astream(initial_state):
                for node_name, node_state in step_output.items():
                    if not isinstance(node_state, dict):
                        continue
                    trace_steps = node_state.get("agent_trace", [])
                    if trace_steps and len(trace_steps) > emitted_trace_count:
                        for step in trace_steps[emitted_trace_count:]:
                            yield SSEEvent(
                                event_type="trace",
                                data={
                                    "tool_name": step["tool_name"],
                                    "input": step["input"],
                                    "output": step["output"],
                                    "timestamp": step["timestamp"],
                                },
                            )
                        emitted_trace_count = len(trace_steps)

                    final_response = node_state.get("final_response", "")
                    if final_response and node_name == "response_synthesiser":
                        words = final_response.split(" ")
                        for word in words:
                            yield SSEEvent(event_type="token", data={"token": word + " "})

                        order_rec = node_state.get("order_recommendation")
                        if order_rec:
                            yield SSEEvent(event_type="order", data=order_rec)

                        yield SSEEvent(event_type="done", data={})
                        return

        except Exception as exc:
            logger.error("MarketMateAgent.run error: %s", exc, exc_info=True)
            yield SSEEvent(event_type="error", data={"message": str(exc)})
