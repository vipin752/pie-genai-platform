"""Market Intelligence Agent — Section 6.3.

Calls the two read-only PIE Trader tools (trade card, risk state) for a
symbol it extracts from the user's text, and synthesizes a plain-text
answer from their REAL output. "Synthesize" here means deterministic
templating over real numbers, not natural-language generation - there is
no working model to generate prose with yet (Stage C). If a tool call
fails (gateway unreachable, no signal, etc.) that is reported honestly
in the answer, never silently dropped or replaced with invented numbers.
"""

from __future__ import annotations

from pie_genai.agents.base import AgentResult, AgentSpec
from pie_genai.integrations.pie_trader.dto import RiskStateResult, TradeCardResult
from pie_genai.tools.base import PermissionLevel, ToolExecutionResult
from pie_genai.tools.execution import ToolExecutor
from pie_genai.tools.pie_trader_tools import (
    MARKET_INTELLIGENCE_AGENT_ID,
    TOOL_RISK_STATE,
    TOOL_TRADE_CARD,
)

# Checked longest-keyword-first so "banknifty" never gets misread as the
# plain "nifty" substring inside it.
_SYMBOL_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("bank nifty", "BANKNIFTY"),
    ("banknifty", "BANKNIFTY"),
    ("finnifty", "FINNIFTY"),
    ("midcpnifty", "MIDCPNIFTY"),
    ("sensex", "SENSEX"),
    ("nifty", "NIFTY"),
)


def extract_symbol(text: str) -> str:
    lowered = text.lower()
    for keyword, symbol in _SYMBOL_KEYWORDS:
        if keyword in lowered:
            return symbol
    return "NIFTY"  # project's initial market priority (master prompt Section 5)


class MarketIntelligenceAgent:
    spec = AgentSpec(
        id=MARKET_INTELLIGENCE_AGENT_ID,
        name="Market Intelligence Agent",
        description="Answers questions about one index's current trade card "
        "and risk state using backend/pietrader-gateway's real, read-only data.",
        domain="TRADING_INTELLIGENCE",
        version="1.0.0",
        capabilities=("trade_card_lookup", "risk_state_lookup"),
        tools_allowed=frozenset({TOOL_TRADE_CARD, TOOL_RISK_STATE}),
        permission_level=PermissionLevel.READ,
        timeout_s=10.0,
    )

    def __init__(self, executor: ToolExecutor) -> None:
        self._executor = executor

    async def run(self, user_text: str) -> AgentResult:
        symbol = extract_symbol(user_text)

        card_result = await self._executor.execute(TOOL_TRADE_CARD, self.spec.id, symbol=symbol)
        risk_result = await self._executor.execute(TOOL_RISK_STATE, self.spec.id)

        text = _synthesize(symbol, card_result, risk_result)
        return AgentResult(text=text, tool_calls=[card_result, risk_result])


def _tool_failure_reason(result: ToolExecutionResult) -> str:
    return result.reason_if_denied or result.error or "unknown error"


def _synthesize(
    symbol: str, card_result: ToolExecutionResult, risk_result: ToolExecutionResult
) -> str:
    lines = [f"Market intelligence for {symbol} (from backend/pietrader-gateway, real data):"]

    if not card_result.success:
        lines.append(f"- Trade card unavailable: {_tool_failure_reason(card_result)}")
    else:
        card_output: TradeCardResult = card_result.output
        card = card_output.card
        if card.status != "OK":
            detail = card.message or card.error or "no further detail"
            lines.append(f"- Trade card status: {card.status} ({detail})")
        else:
            lines.append(f"- Regime: {card.regime}, action: {card.action}, confidence: {card.confidence}")
            if card.option:
                lines.append(f"- Selected option: {card.option.selected} @ LTP {card.option.ltp}")
            if card.risk:
                lines.append(
                    f"- Risk:Reward {card.risk.risk_reward_ratio}:1, "
                    f"potential return ₹{card.risk.potential_return_inr:,.2f}, "
                    f"max loss ₹{card.risk.max_loss_inr:,.2f}"
                )

    if not risk_result.success:
        lines.append(f"- Risk state unavailable: {_tool_failure_reason(risk_result)}")
    else:
        risk_output: RiskStateResult = risk_result.output
        match = next((r for r in risk_output.risk_state if r.symbol == symbol), None)
        if match is None:
            lines.append(f"- No risk-state entry found for {symbol} in the gateway's response")
        else:
            lines.append(
                f"- Today: PnL ₹{match.daily_pnl:,.2f}, {match.daily_trade_count} trade(s), "
                f"{'LOCKED' if match.is_locked else 'not locked'}, "
                f"{'MAX LOSS BREACHED' if match.is_max_loss_breached else 'within loss limit'}"
            )

    return "\n".join(lines)
