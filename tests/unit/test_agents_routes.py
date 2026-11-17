from fastapi.testclient import TestClient

from pie_genai.api.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_agents_reports_the_one_registered_agent():
    resp = _client().get("/api/v1/agents")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == "market_intelligence_agent"
    assert "pie_trader.trade_card" in body[0]["tools_allowed"]
    assert "pie_trader.risk_state" in body[0]["tools_allowed"]
    assert body[0]["permission_level"] == "READ"


def test_get_unknown_agent_is_404():
    resp = _client().get("/api/v1/agents/no_such_agent")
    assert resp.status_code == 404


def test_agent_health_reports_both_declared_tools_registered():
    resp = _client().get("/api/v1/agents/market_intelligence_agent/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "available"
    assert body["tools_registered"] == 2
    assert body["tools_missing"] == []


def test_market_analysis_message_is_completed_by_the_agent_not_failed():
    """The real app's gateway URL (localhost:8080) has nothing listening
    in this sandbox, so the agent's tool calls fail - but the RUN still
    completes, with that failure reported honestly in the answer. This is
    the key difference Stage E makes versus Stage D alone: a market
    question no longer always falls through to the always-failing model
    path.
    """
    client = _client()
    conversation_id = client.post("/api/v1/conversations").json()["id"]

    submitted = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "what's NIFTY looking like"},
    )
    body = submitted.json()
    assert body["status"] == "completed"

    run = client.get(f"/api/v1/runs/{body['run_id']}").json()
    assert run["status"] == "completed"
    assert run["error"] is None
    assert "Market intelligence for NIFTY" in run["result_text"]
    assert "Trade card unavailable" in run["result_text"]

    events = client.get(f"/api/v1/runs/{body['run_id']}/events").text
    assert "tool.failed" in events
    assert "run.completed" in events

    messages = client.get(f"/api/v1/conversations/{conversation_id}/messages").json()
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert "Market intelligence for NIFTY" in messages[1]["content"]


def test_general_question_still_falls_through_to_the_unconfigured_model():
    client = _client()
    conversation_id = client.post("/api/v1/conversations").json()["id"]

    submitted = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "hello there"}
    )
    body = submitted.json()
    assert body["status"] == "failed"
