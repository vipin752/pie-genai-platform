from fastapi.testclient import TestClient

from pie_genai.api.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_models_reports_the_one_registered_model():
    resp = _client().get("/api/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "pie-genai-core"
    assert "simple_conversation" in body[0]["task_types"]


def test_models_health_reports_skeleton_as_not_configured():
    resp = _client().get("/api/v1/models/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pie-genai-core"]["configured"] is False


def test_models_usage_starts_at_zero_calls():
    resp = _client().get("/api/v1/models/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["models"]["pie-genai-core"]["calls"] == 0
    assert body["models"]["pie-genai-core"]["success_rate"] is None
