"""Unit test cho src/agent/store.py — lưu trữ hội thoại/tin nhắn, chạy trên
DB thật (bảng conversations/messages, đã có sẵn từ Ngày 1).
"""

from __future__ import annotations

from src.agent.store import (
    append_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
    to_llm_message,
)


def test_create_and_get_conversation():
    conv = create_conversation(title="test hoi thoai")
    assert conv["title"] == "test hoi thoai"

    fetched = get_conversation(conv["id"])
    assert fetched is not None
    assert fetched["id"] == conv["id"]

    delete_conversation(conv["id"])


def test_get_conversation_unknown_returns_none():
    assert get_conversation("00000000-0000-0000-0000-000000000000") is None


def test_list_conversations_includes_created_one():
    conv = create_conversation()
    ids = [c["id"] for c in list_conversations(limit=200)]
    assert conv["id"] in ids
    delete_conversation(conv["id"])


def test_append_and_list_messages_round_trip():
    conv = create_conversation()
    append_message(conv["id"], "user", content="Cho toi thong tin tau X")
    append_message(
        conv["id"],
        "assistant",
        content=None,
        tool_calls_json=[
            {"id": "call_1", "type": "function", "function": {"name": "search_vessel", "arguments": '{"query": "X"}'}}
        ],
    )
    append_message(conv["id"], "tool", content='[{"shipname": "X"}]', tool_call_id="call_1")

    rows = list_messages(conv["id"])
    assert [r["role"] for r in rows] == ["user", "assistant", "tool"]
    assert rows[1]["tool_calls_json"][0]["function"]["name"] == "search_vessel"
    assert rows[2]["tool_call_id"] == "call_1"

    delete_conversation(conv["id"])


def test_delete_conversation_cascades_messages():
    conv = create_conversation()
    append_message(conv["id"], "user", content="hi")

    deleted = delete_conversation(conv["id"])
    assert deleted is True
    assert get_conversation(conv["id"]) is None
    assert list_messages(conv["id"]) == []


def test_delete_conversation_unknown_returns_false():
    assert delete_conversation("00000000-0000-0000-0000-000000000000") is False


def test_to_llm_message_formats_by_role():
    user_row = {"role": "user", "content": "hi", "tool_call_id": None, "tool_calls_json": None}
    assert to_llm_message(user_row) == {"role": "user", "content": "hi"}

    assistant_row = {
        "role": "assistant",
        "content": None,
        "tool_call_id": None,
        "tool_calls_json": [{"id": "call_1", "type": "function", "function": {"name": "x", "arguments": "{}"}}],
    }
    formatted = to_llm_message(assistant_row)
    assert formatted["tool_calls"][0]["id"] == "call_1"

    tool_row = {"role": "tool", "content": "[]", "tool_call_id": "call_1", "tool_calls_json": None}
    formatted_tool = to_llm_message(tool_row)
    assert formatted_tool["tool_call_id"] == "call_1"
    assert "tool_calls" not in formatted_tool
