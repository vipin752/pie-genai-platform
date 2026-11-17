"""Wraps Stage G's read-only PieTraderClient as registered Tools.

Only GET/read methods are wrapped - PieTraderClient itself has no method
for the gateway's write endpoints (see
integrations/pie_trader/client.py's module docstring), and
ToolRegistry.register() separately refuses anything at
PermissionLevel.FINANCIAL_ACTION even if that changed. Two independent
enforcement points for the same rule, on purpose.
"""

from __future__ import annotations

from pie_genai.integrations.pie_trader import PieTraderClient
from pie_genai.tools.base import PermissionLevel, ToolSpec

MARKET_INTELLIGENCE_AGENT_ID = "market_intelligence_agent"

TOOL_TRADE_CARD = "pie_trader.trade_card"
TOOL_DASHBOARD = "pie_trader.dashboard"
TOOL_POSITIONS = "pie_trader.positions"
TOOL_RISK_STATE = "pie_trader.risk_state"


def build_pie_trader_tools(client: PieTraderClient) -> list[ToolSpec]:
    return [
        ToolSpec(
            id=TOOL_TRADE_CARD,
            name="Get Trade Card",
            description="Strike, direction, confidence, risk/reward and potential "
            "return for one index, from backend/pietrader-gateway's real "
            "TradeCardMapper output.",
            version="1.0.0",
            permission_level=PermissionLevel.READ,
            data_classification="market-data",
            timeout_s=5.0,
            allowed_agents=frozenset({MARKET_INTELLIGENCE_AGENT_ID}),
            handler=client.get_trade_card,
        ),
        ToolSpec(
            id=TOOL_DASHBOARD,
            name="Get Dashboard",
            description="System-wide trading mode, active position count and a "
            "per-symbol summary (PnL, trade count, lock/breach flags).",
            version="1.0.0",
            permission_level=PermissionLevel.READ,
            data_classification="market-data",
            timeout_s=5.0,
            allowed_agents=frozenset({MARKET_INTELLIGENCE_AGENT_ID}),
            handler=client.get_dashboard,
        ),
        ToolSpec(
            id=TOOL_POSITIONS,
            name="Get Positions",
            description="Currently open positions with entry/current price, stop, "
            "target and realised/unrealised PnL. Read-only - cannot modify a position.",
            version="1.0.0",
            permission_level=PermissionLevel.READ,
            data_classification="portfolio-read",
            timeout_s=5.0,
            allowed_agents=frozenset({MARKET_INTELLIGENCE_AGENT_ID}),
            handler=client.get_positions,
        ),
        ToolSpec(
            id=TOOL_RISK_STATE,
            name="Get Risk State",
            description="Per-symbol risk state: daily PnL, loss %, lock/cooldown/"
            "max-loss-breach flags, trade count vs. limit. Read-only.",
            version="1.0.0",
            permission_level=PermissionLevel.READ,
            data_classification="portfolio-read",
            timeout_s=5.0,
            allowed_agents=frozenset({MARKET_INTELLIGENCE_AGENT_ID}),
            handler=client.get_risk_state,
        ),
    ]
