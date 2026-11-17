"""Exercises the orchestrator directly, with a successful test-double
model so the COMPLETED path (which the default unconfigured skeleton can
never reach) is actually proven, not just the FAILED path HTTP tests
cover against the real default gateway."""

import pytest

from pie_genai.conversations.models import MessageRole, RunStatus
from pie_genai.conversations.store import ConversationStore
from pie_genai.core.orchestrator import Orchestrator, RunAlreadyTerminalError
from pie_genai.llm.gateway import LlmGateway
from pie_genai.llm.providers.base import ModelProvider, ModelRequest, ModelResponse
from pie_genai.llm.registry import ModelRegistry, ModelSpec
from pie_genai.llm.router import TASK_COMPLEX_REASONING, TASK_SIMPLE_CONVERSATION


class _EchoProvider(ModelProvider):
    """Test double only, not a real model - see module docstring."""

    provider_name = "test-double-echo"

    async def invoke(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(text=f"echo: {request.prompt}", tokens=7)


def _orchestrator_with_echo() -> tuple[Orchestrator, ConversationStore]:
    registry = ModelRegistry(
        [
            ModelSpec(
                name="echo-model",
                provider=_EchoProvider(),
                task_types=frozenset({TASK_SIMPLE_CONVERSATION, TASK_COMPLEX_REASONING}),
                context_window_tokens=0,
            )
        ]
    )
    store = ConversationStore()
    orchestrator = Orchestrator(store, LlmGateway(registry))
    return orchestrator, store


async def test_successful_run_completes_and_appends_assistant_message():
    orchestrator, store = _orchestrator_with_echo()
    conv = store.create_conversation()

    run = await orchestrator.handle_user_message(conv.id, "hello there")

    assert run.status == RunStatus.COMPLETED
    assert run.result_text == "echo: hello there"
    assert run.error is None

    messages = store.get_conversation(conv.id).messages
    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[1].content == "echo: hello there"


async def test_successful_run_emits_the_full_event_sequence():
    orchestrator, store = _orchestrator_with_echo()
    conv = store.create_conversation()

    run = await orchestrator.handle_user_message(conv.id, "what's NIFTY doing")

    event_types = [e.type for e in run.events]
    assert event_types == [
        "run.accepted",
        "run.started",
        "intent.classified",
        "plan.created",
        "agent.started",
        "response.completed",
        "run.completed",
    ]
    # "nifty" keyword -> market_analysis intent, not the general-question default.
    intent_event = next(e for e in run.events if e.type == "intent.classified")
    assert intent_event.payload["intent"] == "market_analysis"


async def test_failed_run_never_appends_an_assistant_message():
    class _AlwaysFailsProvider(ModelProvider):
        provider_name = "test-double-fails"

        async def invoke(self, request: ModelRequest) -> ModelResponse:
            from pie_genai.llm.providers.base import ModelProviderError

            raise ModelProviderError("boom", retryable=False)

    registry = ModelRegistry(
        [ModelSpec(name="m", provider=_AlwaysFailsProvider(), task_types=frozenset({TASK_SIMPLE_CONVERSATION}), context_window_tokens=0)]
    )
    store = ConversationStore()
    orchestrator = Orchestrator(store, LlmGateway(registry))
    conv = store.create_conversation()

    run = await orchestrator.handle_user_message(conv.id, "hi")

    assert run.status == RunStatus.FAILED
    assert run.error == "boom"
    assert len(store.get_conversation(conv.id).messages) == 1  # user message only


async def test_cancel_a_terminal_run_raises():
    orchestrator, store = _orchestrator_with_echo()
    conv = store.create_conversation()
    run = await orchestrator.handle_user_message(conv.id, "hi")

    with pytest.raises(RunAlreadyTerminalError):
        orchestrator.cancel(run.id)
