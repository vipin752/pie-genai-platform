import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from pie_genai.api.app import create_app
from pie_genai.api.routes.pie_trader import get_pie_trader_client
from pie_genai.integrations.pie_trader import PieTraderClient

GATEWAY = "http://localhost:8080"


def _client_with_gateway_at(base_url: str) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_pie_trader_client] = lambda: PieTraderClient(base_url=base_url)
    return TestClient(app)


@pytest.mark.respx(base_url=GATEWAY)
def test_trade_card_route_maps_unreachable_gateway_to_503(respx_mock):
    respx_mock.get("/api/trade-card", params={"symbol": "NIFTY"}).mock(
        side_effect=httpx.ConnectError("refused")
    )
    resp = _client_with_gateway_at(GATEWAY).get("/api/v1/integrations/pie-trader/trade-card")
    assert resp.status_code == 503
    assert "pie-trader" in resp.json()["detail"].lower() or "reach" in resp.json()["detail"].lower()


@pytest.mark.respx(base_url=GATEWAY)
def test_health_route_reports_unreachable_without_raising(respx_mock):
    respx_mock.get("/actuator/health").mock(side_effect=httpx.ConnectError("refused"))
    resp = _client_with_gateway_at(GATEWAY).get("/api/v1/integrations/pie-trader/health")
    assert resp.status_code == 200
    assert resp.json() == {"service": "backend/pietrader-gateway", "reachable": False}
