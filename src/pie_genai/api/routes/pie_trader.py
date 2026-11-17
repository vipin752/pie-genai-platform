"""Stage G — PIE Trader integration, exposed as read-only HTTP endpoints
so the integration can be exercised before any agent/tool framework
(Stage E) exists to call it. No endpoint here can place, modify or cancel
an order — see pie_genai.integrations.pie_trader.client's module docstring
for why that's a hard boundary, not an oversight.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from pie_genai.config import Settings, get_settings
from pie_genai.integrations.pie_trader import (
    DashboardResult,
    PieTraderClient,
    PieTraderIntegrationError,
    PositionsResult,
    RiskStateResult,
    TradeCardResult,
)

router = APIRouter(prefix="/api/v1/integrations/pie-trader", tags=["pie-trader-integration"])


def get_pie_trader_client(settings: Settings = Depends(get_settings)) -> PieTraderClient:
    return PieTraderClient(
        base_url=settings.pie_trader_gateway_url,
        api_token=settings.pie_trader_api_token,
    )


@router.get("/health")
async def pie_trader_health(client: PieTraderClient = Depends(get_pie_trader_client)) -> dict:
    reachable = await client.health()
    return {"service": "backend/pietrader-gateway", "reachable": reachable}


@router.get("/trade-card", response_model=TradeCardResult)
async def trade_card(
    symbol: str = "NIFTY",
    client: PieTraderClient = Depends(get_pie_trader_client),
) -> TradeCardResult:
    try:
        return await client.get_trade_card(symbol)
    except PieTraderIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/dashboard", response_model=DashboardResult)
async def dashboard(client: PieTraderClient = Depends(get_pie_trader_client)) -> DashboardResult:
    try:
        return await client.get_dashboard()
    except PieTraderIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/positions", response_model=PositionsResult)
async def positions(client: PieTraderClient = Depends(get_pie_trader_client)) -> PositionsResult:
    try:
        return await client.get_positions()
    except PieTraderIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/risk", response_model=RiskStateResult)
async def risk_state(client: PieTraderClient = Depends(get_pie_trader_client)) -> RiskStateResult:
    try:
        return await client.get_risk_state()
    except PieTraderIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
