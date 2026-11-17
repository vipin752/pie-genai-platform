"""Conversation and message APIs — Section 14.1 and the Section 15
request/response contract.

Pagination (Section 14.1's own requirement for the messages endpoint) is
FUTURE PLAN: there is no real conversation volume yet to need it, and
adding it speculatively would be exactly the kind of unjustified
complexity the master prompt warns against.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from pie_genai.api.schemas.conversations import (
    ConversationResponse,
    MessageResponse,
    SubmitMessageRequest,
    SubmitMessageResponse,
)
from pie_genai.conversations.store import ConversationNotFoundError, ConversationStore
from pie_genai.core.orchestrator import Orchestrator

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _store(request: Request) -> ConversationStore:
    return request.app.state.conversation_store


def _orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(request: Request) -> ConversationResponse:
    conv = _store(request).create_conversation()
    return ConversationResponse(id=conv.id, created_at=conv.created_at, message_count=0)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(request: Request) -> list[ConversationResponse]:
    return [
        ConversationResponse(id=c.id, created_at=c.created_at, message_count=len(c.messages))
        for c in _store(request).list_conversations()
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, request: Request) -> ConversationResponse:
    try:
        conv = _store(request).get_conversation(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc
    return ConversationResponse(id=conv.id, created_at=conv.created_at, message_count=len(conv.messages))


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, request: Request) -> None:
    _store(request).delete_conversation(conversation_id)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(conversation_id: str, request: Request) -> list[MessageResponse]:
    try:
        conv = _store(request).get_conversation(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc
    return [
        MessageResponse(id=m.id, role=m.role.value, content=m.content, created_at=m.created_at)
        for m in conv.messages
    ]


@router.post("/{conversation_id}/messages", response_model=SubmitMessageResponse, status_code=202)
async def submit_message(
    conversation_id: str, body: SubmitMessageRequest, request: Request
) -> SubmitMessageResponse:
    try:
        _store(request).get_conversation(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc

    # Runs synchronously today - see core/orchestrator.py's module
    # docstring. The 202/run_id/events_url shape is Section 15's async
    # contract regardless, so API consumers never need to change when
    # this becomes genuinely async (Stage E/F, once a step can be
    # long-running).
    run = await _orchestrator(request).handle_user_message(conversation_id, body.content)

    return SubmitMessageResponse(
        conversation_id=conversation_id,
        message_id=run.message_id,
        run_id=run.id,
        status=run.status.value,
        events_url=f"/api/v1/runs/{run.id}/events",
        created_at=datetime.now(timezone.utc),
    )
