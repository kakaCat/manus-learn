"""Chat-related data models."""

from typing import List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request model for REST API."""

    message: str
    chat_history: List[dict] = []
    agent_type: str = "coordinator"  # DeepAgent subagent: manager, shell, filesystem, chrome, coordinator


class ChatResponse(BaseModel):
    """Chat response model."""

    status: str
    response: str | None = None
    error: str | None = None
    thread_id: str | None = None


class WebSocketMessage(BaseModel):
    """WebSocket message from client."""

    message: str
