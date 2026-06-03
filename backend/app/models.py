import time
import uuid
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class AgentTraceStep(BaseModel):
    tool_name: str
    input: str
    output: str
    timestamp: float = Field(default_factory=time.time)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_trace: List[AgentTraceStep] = Field(default_factory=list)


class OrderItem(BaseModel):
    item: str
    quantity: float
    unit: str
    vs_normal_pct: float
    reasoning: str
    confidence: Literal["High", "Medium", "Low"]
    estimated_cost_aud: float
    estimated_revenue_aud: float


class OrderRecommendation(BaseModel):
    items: List[OrderItem]
    total_cost_aud: float
    total_revenue_aud: float
    order_by: str
    confidence: str
    notes: str


class SSEEvent(BaseModel):
    event_type: Literal["trace", "token", "order", "done", "error"]
    data: Union[Dict, str]
