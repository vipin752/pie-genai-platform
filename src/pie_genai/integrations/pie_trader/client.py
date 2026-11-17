"""Read-only client for backend/pietrader-gateway.

Deliberately exposes only GET/read endpoints. Section 19 of the master
prompt is absolute: GenAI must never submit a broker order, bypass the
Risk Manager, or independently change trading/risk/capital state. The
gateway's write endpoints (POST /api/mode, /api/manual-trade,
/api/squareoff) have no client method here on purpose — this is not an
oversight to "add later", it is the Stage G scope boundary itself.

Every call that reaches the gateway successfully returns real data with
DataProvenance attached. A call that cannot reach the gateway raises
PieTraderIntegrationError rather than returning fabricated or stale data
silently — per Section 18, "if the source is unavailable, report that
clearly."
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from pie_genai.integrations.pie_trader.dto import (
    Dashboard,
    DashboardResult,
    DataProvenance,
    Position,
    PositionsResult,
    RiskStateEntry,
    RiskStateResult,
    TradeCard,
    TradeCardResult,
)


class PieTraderIntegrationError(RuntimeError):
    """Raised for any failure talking to backend/pietrader-gateway —
    unreachable, timed out, or an unexpected response shape. Callers must
    treat this as "no data available", never fall back to inventing one."""


def _provenance(symbol: str, status: str = "live") -> DataProvenance:
    return DataProvenance(
        instrument=symbol,
        source="pie-trader-gateway",
        fetched_at=datetime.now(timezone.utc),
        status=status,  # type: ignore[arg-type]
    )


class PieTraderClient:
    def __init__(self, base_url: str, api_token: str | None = None, timeout_s: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._timeout_s = timeout_s

    def _headers(self) -> dict[str, str]:
        # backend/pietrader-gateway has no real authentication yet
        # (SecurityConfig permits all requests) — this header is sent
        # anyway so nothing here needs to change once that lands.
        if self._api_token:
            return {"Authorization": f"Bearer {self._api_token}"}
        return {}

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as exc:
            raise PieTraderIntegrationError(f"Timed out calling {url}") from exc
        except httpx.ConnectError as exc:
            raise PieTraderIntegrationError(f"Could not reach pie-trader gateway at {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise PieTraderIntegrationError(
                f"{url} returned {exc.response.status_code}"
            ) from exc
        except ValueError as exc:  # non-JSON body
            raise PieTraderIntegrationError(f"{url} did not return valid JSON") from exc

    async def get_trade_card(self, symbol: str) -> TradeCardResult:
        raw = await self._get("/api/trade-card", params={"symbol": symbol})
        card = TradeCard.model_validate(raw)
        return TradeCardResult(card=card, provenance=_provenance(symbol))

    async def get_dashboard(self) -> DashboardResult:
        raw = await self._get("/api/dashboard")
        dashboard = Dashboard.model_validate(raw)
        return DashboardResult(dashboard=dashboard, provenance=_provenance("ALL"))

    async def get_positions(self) -> PositionsResult:
        raw = await self._get("/api/positions")
        positions = [Position.model_validate(p) for p in raw]
        return PositionsResult(positions=positions, provenance=_provenance("ALL"))

    async def get_risk_state(self) -> RiskStateResult:
        raw = await self._get("/api/risk")
        entries = [RiskStateEntry.model_validate(r) for r in raw]
        return RiskStateResult(risk_state=entries, provenance=_provenance("ALL"))

    async def health(self) -> bool:
        """True only if the gateway's own actuator reports it up. Never
        guesses; a failure here means `reachable: false`, not `True`."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout_s) as client:
                resp = await client.get(f"{self._base_url}/actuator/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
