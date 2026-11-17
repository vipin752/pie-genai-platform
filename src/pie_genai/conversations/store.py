"""In-memory conversation/run store. See models.py's module docstring for
why this is memory-only and what that means."""

from __future__ import annotations

from pie_genai.conversations.models import Conversation, Message, Run


class ConversationNotFoundError(KeyError):
    pass


class RunNotFoundError(KeyError):
    pass


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._runs: dict[str, Run] = {}

    def create_conversation(self) -> Conversation:
        conv = Conversation()
        self._conversations[conv.id] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> Conversation:
        try:
            return self._conversations[conversation_id]
        except KeyError as exc:
            raise ConversationNotFoundError(conversation_id) from exc

    def list_conversations(self) -> list[Conversation]:
        return sorted(self._conversations.values(), key=lambda c: c.created_at, reverse=True)

    def delete_conversation(self, conversation_id: str) -> None:
        self._conversations.pop(conversation_id, None)

    def add_message(self, conversation_id: str, message: Message) -> None:
        self.get_conversation(conversation_id).messages.append(message)

    def save_run(self, run: Run) -> None:
        self._runs[run.id] = run

    def get_run(self, run_id: str) -> Run:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise RunNotFoundError(run_id) from exc
