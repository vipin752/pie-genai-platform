"""DTOs for backend/pietrader-gateway's REST contract.

Field names and nesting below are copied from the real, already-tested
response shapes in that repository (not invented):
  - GET /api/trade-card  -> com.pietrader.mapper.TradeCardMapper.toTradeCard()
  - GET /api/dashboard   -> com.pietrader.controller.DashboardController.dashboard()
  - GET /api/positions   -> DashboardController.positions()
  - GET /api/risk        -> DashboardController.riskState()

`session`, `expiry`, `signals`, `fear_index`, `trading_card` and
`execution_plan` are passed through as plain dicts rather than fully
typed: this adapter has verified `TradeCardMapper`'s top-level fields and
`option`/`risk`/`levels`/`execution` exactly, but not those builders'
internals, and the master prompt's own rule is never to invent a
contract. Extending the strong typing to them is future work once that
part of the gateway is read too.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DataProvenance(BaseModel):
    """Required on every market-data response (master prompt Section 18):
    instrument, source, timestamps, freshness, live/delayed/simulated
    status. Never silently substituted for mock data."""

    instrument: str
    source: Literal["pie-trader-gateway"]
    exchange_timestamp_ms: int | None = None
    fetched_at: datetime
    status: Literal["live", "unavailable"]


class TradeCardOption(BaseModel):
    model_config = ConfigDict(extra="ignore")

    selected: str
    final_strike: str
    override_type: str
    ltp: float
    iv: float
    volume: int
    volume_rank: str
    pcr: float | None = None
    pcr_sentiment: str | None = None


class TradeCardRisk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position_size: str
    sl: str
    target: str
    max_loss: str
    capital: float
    # Computed per-trade levels (added to TradeCardMapper this iteration):
    stop_loss_price: float
    target_price: float
    risk_reward_ratio: float
    max_loss_inr: float
    potential_return_inr: float
    position_status: str
    risk_reason: str
    risk_confidence: str | None = None


class TradeCardLevels(BaseModel):
    model_config = ConfigDict(extra="ignore")

    support: float
    resistance: float
    gamma_flip: float
    call_wall: float
    put_wall: float
    net_gamma: float
    upper_1d: float | None = None
    lower_1d: float | None = None
    atm_iv: float | None = None


class TradeCardExecution(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry_trigger: str
    raw_trigger: str
    breakout_status: str
    entry_signal: str
    entry_type: str
    timing_reason: str
    execution_ready: bool
    block_reason: str
    confirmation: str


class TradeCard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str
    status: Literal["OK", "NO_DATA", "ERROR", "PARSE_ERROR", "NO_SIGNAL"]
    spot: float | None = None
    atm: int | None = None
    timestamp: int | None = None
    regime: str | None = None
    strategy: str | None = None
    action: str | None = None
    direction: str | None = None
    confidence: int | None = None
    session: dict[str, Any] | None = None
    expiry: dict[str, Any] | None = None
    levels: TradeCardLevels | None = None
    execution: TradeCardExecution | None = None
    option: TradeCardOption | None = None
    risk: TradeCardRisk | None = None
    signals: dict[str, Any] | None = None
    reason: list[str] = Field(default_factory=list)
    fear_index: dict[str, Any] | None = None
    trading_card: dict[str, Any] | None = None
    execution_plan: dict[str, Any] | None = None
    message: str | None = None  # present on NO_SIGNAL
    error: str | None = None  # present on PARSE_ERROR


class TradeCardResult(BaseModel):
    """What this integration adapter actually returns — the real
    TradeCard plus the provenance the master prompt requires around it."""

    card: TradeCard
    provenance: DataProvenance


class SymbolSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str
    daily_pnl: float = Field(alias="dailyPnl")
    trades_today: int = Field(alias="tradesToday")
    has_position: bool = Field(alias="hasPosition")
    loss_percent: float = Field(alias="lossPercent")
    max_loss_breached: bool = Field(alias="maxLossBreached")
    is_locked: bool = Field(alias="isLocked")
    has_signal: bool = Field(alias="hasSignal")


class Dashboard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trading_mode: str = Field(alias="tradingMode")
    system_status: str = Field(alias="systemStatus")
    timestamp: int
    active_positions: int = Field(alias="activePositions")
    symbols: list[SymbolSummary]


class DashboardResult(BaseModel):
    dashboard: Dashboard
    provenance: DataProvenance


class Position(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str
    entry_price: float = Field(alias="entryPrice")
    current_price: float = Field(alias="currentPrice")
    stop_loss: float = Field(alias="stopLoss")
    target: float
    trailing_stop: float = Field(alias="trailingStop")
    pnl: float
    rr_achieved: float = Field(alias="rrAchieved")
    position_state: str = Field(alias="positionState")
    strike: str
    direction: str
    order_id: str = Field(alias="orderId")
    entry_time: str | None = Field(default=None, alias="entryTime")


class PositionsResult(BaseModel):
    positions: list[Position]
    provenance: DataProvenance


class RiskStateEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symbol: str
    daily_pnl: float = Field(alias="dailyPnl")
    daily_trade_count: int = Field(alias="dailyTradeCount")
    current_loss_percent: float = Field(alias="currentLossPercent")
    is_max_loss_breached: bool = Field(alias="isMaxLossBreached")
    is_locked: bool = Field(alias="isLocked")
    is_in_cooldown: bool = Field(alias="isInCooldown")
    has_active_position: bool = Field(alias="hasActivePosition")
    capital: float
    max_trades: int = Field(alias="maxTrades")
    trading_mode: str = Field(alias="tradingMode")


class RiskStateResult(BaseModel):
    risk_state: list[RiskStateEntry]
    provenance: DataProvenance
