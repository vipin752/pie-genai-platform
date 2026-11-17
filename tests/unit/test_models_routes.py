import httpx
import pytest
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
    assert body[0]["provider"] == "Ollama (self-hosted, open-weight)"
    assert "simple_conversation" in body[0]["task_types"]


@pytest.mark.respx(base_url="http://localhost:11434")
def test_models_health_reports_real_unreachable_ollama(respx_mock):
    respx_mock.get("/api/tags").mock(side_effect=httpx.ConnectError("refused"))
    resp = _client().get("/api/v1/models/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pie-genai-core"]["reachable"] is False


@pytest.mark.respx(base_url="http://localhost:11434")
def test_models_health_reports_real_reachable_ollama(respx_mock):
    respx_mock.get("/api/tags").mock(return_value=httpx.Response(200, json={"models": []}))
    resp = _client().get("/api/v1/models/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pie-genai-core"]["reachable"] is True


def test_models_usage_starts_at_zero_calls():
    resp = _client().get("/api/v1/models/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["models"]["pie-genai-core"]["calls"] == 0
    assert body["models"]["pie-genai-core"]["success_rate"] is None
