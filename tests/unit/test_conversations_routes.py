"""HTTP-level conversation/run lifecycle against the real default app -
whose one configured model is an unimplemented skeleton, so every run
here legitimately ends FAILED. test_orchestrator.py covers the COMPLETED
path with a successful test-double model."""

from fastapi.testclient import TestClient

from pie_genai.api.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_full_lifecycle_create_submit_fetch_run_and_events():
    client = _client()

    created = client.post("/api/v1/conversations")
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    submitted = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "hello"}
    )
    assert submitted.status_code == 202
    body = submitted.json()
    assert body["conversation_id"] == conversation_id
    run_id = body["run_id"]
    assert body["events_url"] == f"/api/v1/runs/{run_id}/events"
    # Synchronous today (see orchestrator module docstring) - already terminal.
    assert body["status"] == "failed"

    run_resp = client.get(f"/api/v1/runs/{run_id}")
    assert run_resp.status_code == 200
    run_body = run_resp.json()
    assert run_body["status"] == "failed"
    assert "not configured yet" in run_body["error"]

    events_resp = client.get(f"/api/v1/runs/{run_id}/events")
    assert events_resp.status_code == 200
    assert "run.accepted" in events_resp.text
    assert "run.failed" in events_resp.text

    messages = client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    message_bodies = messages.json()
    assert len(message_bodies) == 1  # user message only - no fabricated assistant reply
    assert message_bodies[0]["role"] == "user"


def test_submit_message_to_unknown_conversation_is_404():
    resp = _client().post("/api/v1/conversations/conv_doesnotexist/messages", json={"content": "hi"})
    assert resp.status_code == 404


def test_get_unknown_run_is_404():
    resp = _client().get("/api/v1/runs/run_doesnotexist")
    assert resp.status_code == 404


def test_cancel_an_already_failed_run_is_409():
    client = _client()
    conversation_id = client.post("/api/v1/conversations").json()["id"]
    run_id = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "hi"}
    ).json()["run_id"]

    resp = client.post(f"/api/v1/runs/{run_id}/cancel")
    assert resp.status_code == 409


def test_delete_conversation_then_get_is_404():
    client = _client()
    conversation_id = client.post("/api/v1/conversations").json()["id"]

    assert client.delete(f"/api/v1/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404


def test_list_conversations_includes_created_ones():
    client = _client()
    first = client.post("/api/v1/conversations").json()["id"]
    second = client.post("/api/v1/conversations").json()["id"]

    ids = [c["id"] for c in client.get("/api/v1/conversations").json()]
    assert first in ids
    assert second in ids
