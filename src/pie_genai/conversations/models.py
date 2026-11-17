"""Conversation/message/run domain model — Section 14.1/14.2's shapes.

In-memory only right now (see store.py) — no database is wired up yet
(Stage F/persistence). State here does not survive a restart, and there
is exactly one process's worth of it. That is a stated limitation, not a
design goal: Section 25 names PostgreSQL as the eventual authoritative
store for all of this.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _id(prefix: str) -> str:
    # Opaque IDs per Section 15 - never a raw database primary key.
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    conversation_id: str
    role: MessageRole
    content: str
    id: str = field(default_factory=lambda: _id("msg"))
    created_at: datetime = field(default_factory=_now)


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: _id("conv"))
    created_at: datetime = field(default_factory=_now)
    messages: list[Message] = field(default_factory=list)


@dataclass
class RunEvent:
    """Section 16's event shape. `type` values are the subset of Section
    16's list this orchestrator actually emits — see orchestrator.py."""

    run_id: str
    type: str
    payload: dict
    id: str = field(default_factory=lambda: _id("evt"))
    created_at: datetime = field(default_factory=_now)


@dataclass
class Run:
    conversation_id: str
    message_id: str
    id: str = field(default_factory=lambda: _id("run"))
    status: RunStatus = RunStatus.ACCEPTED
    created_at: datetime = field(default_factory=_now)
    completed_at: datetime | None = None
    result_text: str | None = None
    error: str | None = None
    events: list[RunEvent] = field(default_factory=list)
    cancel_requested: bool = False

    def emit(self, type_: str, payload: dict) -> None:
        self.events.append(RunEvent(run_id=self.id, type=type_, payload=payload))
