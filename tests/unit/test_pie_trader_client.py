"""Tests the PieTraderClient against mocked HTTP responses shaped exactly
like backend/pietrader-gateway's real, already-tested endpoints (see
dto.py's module docstring for where each shape comes from).

This is a MOCKED-contract test, not a live round-trip against a running
gateway — that distinction matters per the master prompt's own rule to
distinguish mocked tests from real validation. A live round-trip is
tracked as NOT VERIFIED in docs/architecture/SYSTEM_ARCHITECTURE.md.
"""

import httpx
import pytest
import respx

from pie_genai.integrations.pie_trader import PieTraderClient, PieTraderIntegrationError

GATEWAY = "http://localhost:8080"

# Exact shape TradeCardMapper.toTradeCard() returns on a healthy symbol.
TRADE_CARD_OK = {
    "symbol": "NIFTY",
    "spot": 24510.0,
    "atm": 24500,
    "timestamp": 1731830400000,
    "regime": "Trending Bullish",
    "strategy": "sweep_bos",
    "action": "EXECUTE",
    "direction": "Bullish CE",
    "confidence": 78,
    "session": {"phase": "MID_SESSION"},
    "expiry": {"daysToExpiry": 3},
    "levels": {
        "support": 24400.0,
        "resistance": 24650.0,
        "gamma_flip": 24550.0,
        "call_wall": 24700,
        "put_wall": 24300,
        "net_gamma": 1200.0,
    },
    "execution": {
        "entry_trigger": "Break 24550",
        "raw_trigger": "24550",
        "breakout_status": "CONFIRMED",
        "entry_signal": "BREAKOUT",
        "entry_type": "MOMENTUM",
        "timing_reason": "Volume confirmed",
        "execution_ready": True,
        "block_reason": "—",
        "confirmation": "Volume + Breakout + Structure",
    },
    "option": {
        "selected": "NIFTY24NOV24500CE",
        "final_strike": "NIFTY24NOV24500CE",
        "override_type": "NONE",
        "ltp": 186.6,
        "iv": 14.2,
        "volume": 125000,
        "volume_rank": "1",
        "pcr": 1.12,
        "pcr_sentiment": "Bullish",
    },
    "risk": {
        "position_size": "1 lot (75 qty)",
        "sl": "Option SL 25%",
        "target": "RR 1:2",
        "max_loss": "1% capital (₹2000)",
        "capital": 200000.0,
        "stop_loss_price": 139.95,
        "target_price": 280.0,
        "risk_reward_ratio": 2.0,
        "max_loss_inr": 3498.75,
        "potential_return_inr": 6997.5,
        "position_status": "ELIGIBLE",
        "risk_reason": "—",
        "risk_confidence": "HIGH",
    },
    "signals": {"confidence_score": 78, "confidence_level": "HIGH"},
    "reason": ["📦 Compression detected — breakout imminent"],
    "fear_index": {"value": 22},
    "trading_card": {"session": "Session 2"},
    "execution_plan": {"phase": "ENTRY"},
    "status": "OK",
}


@pytest.mark.respx(base_url=GATEWAY)
async def test_get_trade_card_parses_real_shape_and_attaches_provenance(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        return_value=httpx.Response(200, json=TRADE_CARD_OK)
    )
    client = PieTraderClient(base_url=GATEWAY)

    result = await client.get_trade_card("NIFTY")

    assert result.card.status == "OK"
    assert result.card.option.selected == "NIFTY24NOV24500CE"
    assert result.card.risk.risk_reward_ratio == 2.0
    assert result.card.risk.potential_return_inr == 6997.5
    assert result.provenance.source == "pie-trader-gateway"
    assert result.provenance.status == "live"
    assert result.provenance.instrument == "NIFTY"


@pytest.mark.respx(base_url=GATEWAY)
async def test_get_trade_card_no_signal_status_passes_through(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "BANKNIFTY"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "symbol": "BANKNIFTY",
                "status": "NO_SIGNAL",
                "message": "No signal available.",
                "timestamp": 1731830400000,
            },
        )
    )
    client = PieTraderClient(base_url=GATEWAY)

    result = await client.get_trade_card("BANKNIFTY")

    assert result.card.status == "NO_SIGNAL"
    assert result.card.option is None
    assert result.card.risk is None


@pytest.mark.respx(base_url=GATEWAY)
async def test_unreachable_gateway_raises_instead_of_fabricating_data(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        side_effect=httpx.ConnectError("refused")
    )
    client = PieTraderClient(base_url=GATEWAY)

    with pytest.raises(PieTraderIntegrationError):
        await client.get_trade_card("NIFTY")


@pytest.mark.respx(base_url=GATEWAY)
async def test_timeout_raises_pie_trader_integration_error(respx_mock):
    respx_mock.get("/api/dashboard").mock(side_effect=httpx.TimeoutException("timed out"))
    client = PieTraderClient(base_url=GATEWAY)

    with pytest.raises(PieTraderIntegrationError):
        await client.get_dashboard()


@pytest.mark.respx(base_url=GATEWAY)
async def test_get_dashboard_parses_real_shape(respx_mock):
    respx_mock.get("/api/dashboard").mock(
        return_value=httpx.Response(
            200,
            json={
                "tradingMode": "PAPER",
                "systemStatus": "RUNNING",
                "timestamp": 1731830400000,
                "activePositions": 1,
                "symbols": [
                    {
                        "symbol": "NIFTY",
                        "dailyPnl": 1250.5,
                        "tradesToday": 2,
                        "hasPosition": True,
                        "lossPercent": 0.0,
                        "maxLossBreached": False,
                        "isLocked": False,
                        "hasSignal": True,
                    }
                ],
            },
        )
    )
    client = PieTraderClient(base_url=GATEWAY)

    result = await client.get_dashboard()

    assert result.dashboard.trading_mode == "PAPER"
    assert result.dashboard.symbols[0].daily_pnl == 1250.5


@pytest.mark.respx(base_url=GATEWAY)
async def test_get_risk_state_parses_real_shape(respx_mock):
    respx_mock.get("/api/risk").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "symbol": "NIFTY",
                    "dailyPnl": -500.0,
                    "dailyTradeCount": 1,
                    "currentLossPercent": 0.25,
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
    client = PieTraderClient(base_url=GATEWAY)

    result = await client.get_risk_state()

    assert result.risk_state[0].is_max_loss_breached is False
    assert result.risk_state[0].capital == 200000.0


@pytest.mark.respx(base_url=GATEWAY)
async def test_health_false_when_actuator_unreachable(respx_mock):
    respx_mock.get("/actuator/health").mock(side_effect=httpx.ConnectError("refused"))
    client = PieTraderClient(base_url=GATEWAY)

    assert await client.health() is False


@pytest.mark.respx(base_url=GATEWAY)
async def test_health_true_when_actuator_reports_up(respx_mock):
    respx_mock.get("/actuator/health").mock(
        return_value=httpx.Response(200, json={"status": "UP"})
    )
    client = PieTraderClient(base_url=GATEWAY)

    assert await client.health() is True
