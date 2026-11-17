import pytest

from pie_genai.tools.base import PermissionLevel, ToolSpec
from pie_genai.tools.execution import ToolExecutor
from pie_genai.tools.registry import FinancialActionToolRejectedError, ToolRegistry


async def _handler(**kwargs) -> str:
    return "ok"


def _spec(**overrides) -> ToolSpec:
    defaults = dict(
        id="test.tool",
        name="Test Tool",
        description="d",
        version="1.0.0",
        permission_level=PermissionLevel.READ,
        data_classification="market-data",
        timeout_s=1.0,
        allowed_agents=frozenset({"agent_a"}),
        handler=_handler,
    )
    defaults.update(overrides)
    return ToolSpec(**defaults)


def test_registry_rejects_financial_action_tools():
    registry = ToolRegistry()
    with pytest.raises(FinancialActionToolRejectedError):
        registry.register(_spec(permission_level=PermissionLevel.FINANCIAL_ACTION))
    assert registry.get("test.tool") is None


def test_registry_accepts_read_tools():
    registry = ToolRegistry()
    registry.register(_spec())
    assert registry.get("test.tool") is not None
    assert registry.for_agent("agent_a") == [registry.get("test.tool")]
    assert registry.for_agent("agent_b") == []


async def test_executor_allows_a_permitted_agent():
    registry = ToolRegistry()
    registry.register(_spec())
    executor = ToolExecutor(registry)

    result = await executor.execute("test.tool", "agent_a")

    assert result.permitted is True
    assert result.success is True
    assert result.output == "ok"
    assert executor.audit_log.all() == [result]


async def test_executor_denies_an_unlisted_agent():
    registry = ToolRegistry()
    registry.register(_spec())
    executor = ToolExecutor(registry)

    result = await executor.execute("test.tool", "agent_not_allowed")

    assert result.permitted is False
    assert result.success is False
    assert "not in tool" in result.reason_if_denied
    # Denials are audited too, not just successes.
    assert executor.audit_log.all() == [result]


async def test_executor_reports_unregistered_tool():
    registry = ToolRegistry()
    executor = ToolExecutor(registry)

    result = await executor.execute("no.such.tool", "agent_a")

    assert result.permitted is False
    assert "not registered" in result.reason_if_denied


async def test_executor_records_a_handler_failure_without_raising():
    async def _raises(**kwargs):
        raise RuntimeError("downstream exploded")

    registry = ToolRegistry()
    registry.register(_spec(handler=_raises))
    executor = ToolExecutor(registry)

    result = await executor.execute("test.tool", "agent_a")

    assert result.permitted is True
    assert result.success is False
    assert result.error == "downstream exploded"


async def test_executor_times_out_a_slow_handler():
    import asyncio

    async def _slow(**kwargs):
        await asyncio.sleep(1.0)
        return "too slow"

    registry = ToolRegistry()
    registry.register(_spec(handler=_slow, timeout_s=0.01))
    executor = ToolExecutor(registry)

    result = await executor.execute("test.tool", "agent_a")

    assert result.success is False
    assert "TimeoutError" in result.error or result.error == ""
