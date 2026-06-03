import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.demo.responses import DEMO_RESPONSES
from app.models import AgentTraceStep, ChatRequest, ChatResponse, SSEEvent
from app.runtime_config import get_demo_mode
from app.services.agent import MarketMateAgent


logger = logging.getLogger(__name__)

router = APIRouter()

_agent: Optional[MarketMateAgent] = None


def _get_agent() -> MarketMateAgent:
    global _agent
    if _agent is None:
        _agent = MarketMateAgent()
    return _agent


def _normalise_query(query: str) -> str:
    return query.strip().lower().rstrip("?.")


def _find_demo_key(query: str) -> Optional[str]:
    normalised = _normalise_query(query)
    for key in DEMO_RESPONSES:
        if _normalise_query(key) == normalised:
            return key
    for key in DEMO_RESPONSES:
        key_words = set(_normalise_query(key).split())
        query_words = set(normalised.split())
        overlap = len(key_words & query_words) / max(len(key_words), 1)
        if overlap >= 0.7:
            return key
    return None


def _sse_encode(event: SSEEvent) -> str:
    payload = {
        "event_type": event.event_type,
        "data": event.data,
    }
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_demo_response(demo_key: str) -> AsyncGenerator[str, None]:
    demo = DEMO_RESPONSES[demo_key]
    trace_steps = demo.get("trace", [])
    tokens_text = demo.get("tokens", "")
    order = demo.get("order")

    for step in trace_steps:
        event = SSEEvent(
            event_type="trace",
            data={
                "tool_name": step.get("tool_name", ""),
                "input": step.get("input", ""),
                "output": step.get("output", ""),
                "timestamp": step.get("timestamp", 0.0),
            },
        )
        yield _sse_encode(event)
        await asyncio.sleep(0.3)

    words = tokens_text.split(" ")
    for word in words:
        event = SSEEvent(event_type="token", data={"token": word + " "})
        yield _sse_encode(event)
        await asyncio.sleep(0.02)

    if order is not None:
        event = SSEEvent(event_type="order", data=order)
        yield _sse_encode(event)

    yield _sse_encode(SSEEvent(event_type="done", data={}))


_DEMO_FALLBACK = (
    "I'm running in **demo mode**, so I can only answer the 6 preset queries shown below the input. "
    "Try one of the demo chips - for example: *'what should i order this monday'* or "
    "*'are strawberries still worth ordering in june'*.\n\n"
    "To enable live AI responses, set `DEMO_MODE=false` in your `.env` file and restart the server."
)


async def _stream_demo_fallback() -> AsyncGenerator[str, None]:
    words = _DEMO_FALLBACK.split(" ")
    for word in words:
        event = SSEEvent(event_type="token", data={"token": word + " "})
        yield _sse_encode(event)
        await asyncio.sleep(0.02)
    yield _sse_encode(SSEEvent(event_type="done", data={}))


async def _stream_live_response(
    message: str,
    session_id: str,
    conversation_history: list,
) -> AsyncGenerator[str, None]:
    agent = _get_agent()
    try:
        async for sse_event in agent.run(
            query=message,
            conversation_history=conversation_history,
            session_id=session_id,
        ):
            yield _sse_encode(sse_event)
    except Exception as exc:
        logger.error("Live streaming error: %s", exc, exc_info=True)
        error_event = SSEEvent(event_type="error", data={"message": str(exc)})
        yield _sse_encode(error_event)


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("POST /api/chat session=%s message='%s'", session_id, request.message[:80])

    if get_demo_mode():
        demo_key = _find_demo_key(request.message)
        if demo_key:
            demo = DEMO_RESPONSES[demo_key]
            trace_steps = [
                AgentTraceStep(
                    tool_name=s.get("tool_name", ""),
                    input=s.get("input", ""),
                    output=s.get("output", ""),
                    timestamp=s.get("timestamp", 0.0),
                )
                for s in demo.get("trace", [])
            ]
            return ChatResponse(
                response=demo.get("tokens", ""),
                session_id=session_id,
                agent_trace=trace_steps,
            )
        return ChatResponse(
            response=_DEMO_FALLBACK,
            session_id=session_id,
            agent_trace=[],
        )

    agent = _get_agent()
    full_response = ""
    trace_steps_raw = []

    async for sse_event in agent.run(
        query=request.message,
        conversation_history=request.conversation_history,
        session_id=session_id,
    ):
        if sse_event.event_type == "token":
            token = sse_event.data.get("token", "") if isinstance(sse_event.data, dict) else ""
            full_response += token
        elif sse_event.event_type == "trace":
            trace_steps_raw.append(sse_event.data)

    trace_steps = [
        AgentTraceStep(
            tool_name=s.get("tool_name", ""),
            input=s.get("input", ""),
            output=s.get("output", ""),
            timestamp=s.get("timestamp", 0.0),
        )
        for s in trace_steps_raw
        if isinstance(s, dict)
    ]

    return ChatResponse(
        response=full_response.strip(),
        session_id=session_id,
        agent_trace=trace_steps,
    )


@router.get("/api/chat/stream")
async def chat_stream(
    message: str = Query(..., description="The user's message"),
    session_id: Optional[str] = Query(None, description="Session identifier"),
) -> StreamingResponse:
    sid = session_id or str(uuid.uuid4())
    logger.info("GET /api/chat/stream session=%s message='%s'", sid, message[:80])

    if get_demo_mode():
        demo_key = _find_demo_key(message)
        generator = _stream_demo_response(demo_key) if demo_key else _stream_demo_fallback()
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return StreamingResponse(
        _stream_live_response(message, sid, []),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
