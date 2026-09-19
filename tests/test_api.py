"""Integration test cho tầng API (src/api/routes.py) — dùng FastAPI
TestClient trên DB thật, mock đúng ranh giới LLM (chat_stream).
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from main import app
from src.agent import store
from src.models.llm_client import LLMResponse, LLMToolCall

client = TestClient(app)


def _assistant_message(content, tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
            for tc in tool_calls
        ]
    return msg


def _fake_stream(*token_and_final):
    def gen(messages, tools=None):
        for item in token_and_final[:-1]:
            yield {"type": "token", "content": item}
        yield {"type": "final", "response": token_and_final[-1]}

    return gen


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        lines = block.strip().split("\n")
        event_type = lines[0].removeprefix("event: ")
        data = json.loads(lines[1].removeprefix("data: "))
        events.append((event_type, data))
    return events


def test_health_endpoint_reports_ok_when_db_reachable():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}


def test_list_conversations_respects_limit_and_offset():
    ids = [store.create_conversation(title=f"pg-test-{i}")["id"] for i in range(3)]
    try:
        resp = client.get("/conversations", params={"limit": 1, "offset": 0})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        for cid in ids:
            store.delete_conversation(cid)


def test_chat_rejects_empty_message():
    conv = store.create_conversation()
    resp = client.post(f"/conversations/{conv['id']}/chat", json={"message": ""})
    assert resp.status_code == 422
    store.delete_conversation(conv["id"])


def test_create_list_get_delete_conversation_lifecycle():
    resp = client.post("/conversations", json={"title": "test"})
    assert resp.status_code == 200
    conv_id = resp.json()["id"]

    resp = client.get("/conversations")
    assert resp.status_code == 200
    assert any(c["id"] == conv_id for c in resp.json())

    resp = client.get(f"/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.delete(f"/conversations/{conv_id}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    resp = client.get(f"/conversations/{conv_id}/messages")
    assert resp.status_code == 404


def test_get_messages_unknown_conversation_returns_404():
    resp = client.get("/conversations/00000000-0000-0000-0000-000000000000/messages")
    assert resp.status_code == 404


def test_chat_unknown_conversation_returns_404():
    resp = client.post(
        "/conversations/00000000-0000-0000-0000-000000000000/chat", json={"message": "hi"}
    )
    assert resp.status_code == 404


def test_chat_streams_events_and_persists_messages(monkeypatch):
    tool_call = LLMToolCall(id="call_1", name="search_vessel", arguments={"query": "563240200"})
    first = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    second = LLMResponse(
        content="Tau EVER VIVA.", tool_calls=[], raw_assistant_message=_assistant_message("Tau EVER VIVA.")
    )
    calls = [_fake_stream("Đang tra cứu...", first), _fake_stream("Tau EVER VIVA.", second)]
    monkeypatch.setattr(
        "src.agent.agent.chat_stream", lambda messages, tools=None: calls.pop(0)(messages, tools)
    )

    conv = store.create_conversation()
    resp = client.post(f"/conversations/{conv['id']}/chat", json={"message": "tim tau mmsi 563240200"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    event_types = [e[0] for e in events]
    assert event_types == ["token", "tool_call", "token", "done"]
    assert events[-1][1]["answer"] == "Tau EVER VIVA."

    # Kiem tra da persist dung: user + assistant(tool_call) + tool + assistant(final)
    rows = store.list_messages(conv["id"])
    roles = [r["role"] for r in rows]
    assert roles == ["user", "assistant", "tool", "assistant"]
    assert rows[0]["content"] == "tim tau mmsi 563240200"
    assert rows[-1]["content"] == "Tau EVER VIVA."

    store.delete_conversation(conv["id"])


def test_chat_llm_error_persists_user_message_and_streams_error_event(monkeypatch):
    def broken_stream(messages, tools=None):
        raise ConnectionError("khong goi duoc LLM")
        yield  # pragma: no cover

    monkeypatch.setattr("src.agent.agent.chat_stream", broken_stream)

    conv = store.create_conversation()
    resp = client.post(f"/conversations/{conv['id']}/chat", json={"message": "hi"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    assert events[0][0] == "error"

    # Cau hoi cua nguoi dung van phai duoc luu, du LLM loi
    rows = store.list_messages(conv["id"])
    assert [r["role"] for r in rows] == ["user"]

    store.delete_conversation(conv["id"])
