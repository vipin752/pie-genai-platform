"""Exercises MarketIntelligenceAgent end to end against a mocked
PieTraderClient (respx), covering both the real-data synthesis path and
the honest-failure path - the same distinction Stage G's own tests make."""

import httpx
import pytest

from pie_genai.agents.market_intelligence_agent import MarketIntelligenceAgent, extract_symbol
from pie_genai.integrations.pie_trader import PieTraderClient
from pie_genai.tools.execution import ToolExecutor
from pie_genai.tools.pie_trader_tools import build_pie_trader_tools
from pie_genai.tools.registry import ToolRegistry

GATEWAY = "http://localhost:8080"


def _agent() -> MarketIntelligenceAgent:
    client = PieTraderClient(base_url=GATEWAY)
    registry = ToolRegistry()
    for spec in build_pie_trader_tools(client):
        registry.register(spec)
    return MarketIntelligenceAgent(ToolExecutor(registry))


@pytest.mark.parametrize(
    "text,expected",
    [
        ("what about NIFTY gamma today", "NIFTY"),
        ("how's BANKNIFTY looking", "BANKNIFTY"),
        ("bank nifty breakout?", "BANKNIFTY"),
        ("sensex vs nifty", "SENSEX"),  # first keyword match wins (sensex before nifty)
        ("anything interesting happening", "NIFTY"),  # default
    ],
)
def test_extract_symbol(text, expected):
    assert extract_symbol(text) == expected


@pytest.mark.respx(base_url=GATEWAY)
async def test_run_synthesizes_real_data_when_gateway_reachable(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "symbol": "NIFTY",
                "status": "OK",
                "regime": "Trending Bullish",
                "action": "EXECUTE",
                "confidence": 80,
                "option": {
                    "selected": "NIFTY24NOV24500CE",
                    "final_strike": "NIFTY24NOV24500CE",
                    "override_type": "NONE",
                    "ltp": 200.0,
                    "iv": 14.0,
                    "volume": 1000,
                    "volume_rank": "1",
                },
                "risk": {
                    "position_size": "1 lot (75 qty)",
                    "sl": "Option SL 25%",
                    "target": "RR 1:2",
                    "max_loss": "1% capital (₹2000)",
                    "capital": 200000.0,
                    "stop_loss_price": 150.0,
                    "target_price": 300.0,
                    "risk_reward_ratio": 2.0,
                    "max_loss_inr": 3750.0,
                    "potential_return_inr": 7500.0,
                    "position_status": "ELIGIBLE",
                    "risk_reason": "—",
                },
            },
        )
    )
    respx_mock.get("/api/risk").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "symbol": "NIFTY",
                    "dailyPnl": 500.0,
                    "dailyTradeCount": 1,
                    "currentLossPercent": 0.0,
                    "isMaxLossBreached": False,
                    "isLocked": False,
                    "isInCooldown": False,
                    "hasActivePosition": True,
                    "capital": 200000.0,
                    "maxTrades": 3,
                    "tradingMode": "PAPER",
                }
            ],
        )
    )

    result = await _agent().run("what's NIFTY doing")

    assert "Regime: Trending Bullish, action: EXECUTE, confidence: 80" in result.text
    assert "Risk:Reward 2.0:1" in result.text
    assert "potential return ₹7,500.00" in result.text
    assert "PnL ₹500.00" in result.text
    assert "not locked" in result.text
    assert "within loss limit" in result.text
    assert all(tc.success for tc in result.tool_calls)


@pytest.mark.respx(base_url=GATEWAY)
async def test_run_reports_honestly_when_gateway_unreachable(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        side_effect=httpx.ConnectError("refused")
    )
    respx_mock.get("/api/risk").mock(side_effect=httpx.ConnectError("refused"))

    result = await _agent().run("what's NIFTY doing")

    assert "Trade card unavailable" in result.text
    assert "Risk state unavailable" in result.text
    # No fabricated numbers anywhere in a failure response.
    assert "Risk:Reward" not in result.text
    assert all(not tc.success for tc in result.tool_calls)
    assert all(tc.permitted for tc in result.tool_calls)  # denied != failed


@pytest.mark.respx(base_url=GATEWAY)
async def test_run_reports_no_signal_status_honestly(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        return_value=httpx.Response(
            200, json={"symbol": "NIFTY", "status": "NO_SIGNAL", "message": "No signal available."}
        )
    )
    respx_mock.get("/api/risk").mock(return_value=httpx.Response(200, json=[]))

    result = await _agent().run("NIFTY update please")

    assert "Trade card status: NO_SIGNAL (No signal available.)" in result.text
    assert "No risk-state entry found for NIFTY" in result.text
