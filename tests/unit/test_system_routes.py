from fastapi.testclient import TestClient

from pie_genai.api.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_health_ok():
    resp = _client().get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readiness_reports_unconfigured_dependencies():
    resp = _client().get("/api/v1/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["checks"]["database"] == "not_configured"
    assert body["checks"]["redis"] == "not_configured"
    assert body["checks"]["llm_gateway"] == "not_configured"


def test_version_reports_app_name_and_version():
    resp = _client().get("/api/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "pie-genai-platform"
    assert body["version"] == "0.1.0"


def test_capabilities_reflect_only_what_actually_exists():
    resp = _client().get("/api/v1/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    # Every capability flag must stay false until the feature is actually
    # implemented and tested — this test is the guardrail against a flag
    # being flipped to true to match the product vision rather than reality.
    assert body["conversations"] is False
    assert body["agents"] is False
    assert body["rag"] is False
    assert body["memory"] is False
    assert body["workflows"] is False
    # The read-only PIE Trader integration adapter does exist now (Stage G).
    assert body["pie_trader_integration"] is True
