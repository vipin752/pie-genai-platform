from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: str
    created_at: datetime
    message_count: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class SubmitMessageRequest(BaseModel):
    content: str


class SubmitMessageResponse(BaseModel):
    """Section 15's exact async-accept shape."""

    conversation_id: str
    message_id: str
    run_id: str
    status: str
    events_url: str
    created_at: datetime


class RunResponse(BaseModel):
    id: str
    conversation_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    result_text: str | None
    error: str | None
