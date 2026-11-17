"""Run APIs — Section 14.2, and a Section 16-shaped SSE event stream.

Section 16 describes live streaming of a long-running task with
reconnect support (Last-Event-ID). Today's orchestrator runs
synchronously and completes before a client could ever subscribe mid-
flight (see core/orchestrator.py), so GET /events here replays the run's
already-recorded event history in the same wire format rather than
streaming new deltas live. That's an honest, smaller thing than Section
16 asks for - true live streaming and reconnect need a genuinely async,
cancellable run, which needs a real long-running step to exist first
(Stage E/F).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from pie_genai.api.schemas.conversations import RunResponse
from pie_genai.conversations.store import ConversationStore, RunNotFoundError
from pie_genai.core.orchestrator import Orchestrator, RunAlreadyTerminalError

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def _store(request: Request) -> ConversationStore:
    return request.app.state.conversation_store


def _orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, request: Request) -> RunResponse:
    try:
        run = _store(request).get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    return RunResponse(
        id=run.id,
        conversation_id=run.conversation_id,
        status=run.status.value,
        created_at=run.created_at,
        completed_at=run.completed_at,
        result_text=run.result_text,
        error=run.error,
    )


@router.get("/{run_id}/events")
async def run_events(run_id: str, request: Request) -> StreamingResponse:
    try:
        run = _store(request).get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc

    def _replay():
        for event in run.events:
            data = json.dumps(
                {
                    "event_id": event.id,
                    "type": event.type,
                    "run_id": event.run_id,
                    "created_at": event.created_at.isoformat(),
                    "payload": event.payload,
                }
            )
            yield f"id: {event.id}\nevent: {event.type}\ndata: {data}\n\n"

    return StreamingResponse(_replay(), media_type="text/event-stream")


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(run_id: str, request: Request) -> RunResponse:
    try:
        run = _orchestrator(request).cancel(run_id)
    except RunAlreadyTerminalError as exc:
        raise HTTPException(
            status_code=409, detail="run already reached a terminal status, cannot cancel"
        ) from exc
    return RunResponse(
        id=run.id,
        conversation_id=run.conversation_id,
        status=run.status.value,
        created_at=run.created_at,
        completed_at=run.completed_at,
        result_text=run.result_text,
        error=run.error,
    )
