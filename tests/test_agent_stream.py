"""Unit test cho vòng lặp streaming (src/agent/agent.py::run_agent_turn_stream).

Mock chat_stream (generator) — cùng nguyên tắc với test_agent.py: chỉ mock
đúng 1 ranh giới (LLM streaming), tool vẫn chạy DB thật.
"""

from __future__ import annotations

import json

import pytest

from src.agent.agent import MAX_TOOL_ITERATIONS, AgentTurnResult, run_agent_turn_stream
from src.models.llm_client import LLMResponse, LLMToolCall

EVER_VIVA_MMSI = "563240200"


def _assistant_message(content, tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [
            {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
            for tc in tool_calls
        ]
    return msg


def _fake_stream(*token_and_final):
    """Tra ve 1 generator gia lap chat_stream: nhan danh sach (token_events...,
    final_response), yield tung token roi yield final."""

    def gen(messages, tools=None):
        for item in token_and_final[:-1]:
            yield {"type": "token", "content": item}
        yield {"type": "final", "response": token_and_final[-1]}

    return gen


def test_stream_yields_tokens_then_tool_call_then_done(monkeypatch):
    tool_call = LLMToolCall(id="call_1", name="search_vessel", arguments={"query": EVER_VIVA_MMSI})
    first = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    second = LLMResponse(
        content="Tau EVER VIVA.", tool_calls=[], raw_assistant_message=_assistant_message("Tau EVER VIVA.")
    )

    calls = [_fake_stream("Đang ", "tìm...", first), _fake_stream("Tau ", "EVER VIVA.", second)]

    def fake_chat_stream(messages, tools=None):
        return calls.pop(0)(messages, tools)

    monkeypatch.setattr("src.agent.agent.chat_stream", fake_chat_stream)

    result = AgentTurnResult()
    events = list(run_agent_turn_stream([{"role": "user", "content": "tim tau"}], result))

    event_types = [e["event"] for e in events]
    assert event_types == ["token", "token", "tool_call", "token", "token", "done"]
    assert events[-1]["data"]["answer"] == "Tau EVER VIVA."

    tool_results = [m for m in result.new_messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    payload = json.loads(tool_results[0]["content"])
    assert payload[0]["shipname"] == "EVER VIVA"


def test_stream_no_tool_call_yields_done_immediately(monkeypatch):
    response = LLMResponse(content="Xin chao", tool_calls=[], raw_assistant_message=_assistant_message("Xin chao"))
    monkeypatch.setattr("src.agent.agent.chat_stream", _fake_stream("Xin chao", response))

    result = AgentTurnResult()
    events = list(run_agent_turn_stream([{"role": "user", "content": "hi"}], result))

    assert [e["event"] for e in events] == ["token", "done"]
    assert events[-1]["data"]["answer"] == "Xin chao"


def test_stream_llm_exception_yields_error_event_not_raise(monkeypatch):
    def broken_stream(messages, tools=None):
        raise ConnectionError("khong ket noi duoc toi LLM")
        yield  # pragma: no cover - lam cho ham la generator

    monkeypatch.setattr("src.agent.agent.chat_stream", broken_stream)

    result = AgentTurnResult()
    events = list(run_agent_turn_stream([{"role": "user", "content": "hi"}], result))

    assert len(events) == 1
    assert events[0]["event"] == "error"
    assert "khong ket noi" in events[0]["data"]["message"]


def test_stream_tool_error_reported_without_crashing(monkeypatch):
    tool_call = LLMToolCall(id="call_1", name="get_vessel_info", arguments={"vessel_id": "not-a-uuid"})
    first = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    second = LLMResponse(
        content="Da xay ra loi.", tool_calls=[], raw_assistant_message=_assistant_message("Da xay ra loi.")
    )
    calls = [_fake_stream(first), _fake_stream(second)]
    monkeypatch.setattr("src.agent.agent.chat_stream", lambda messages, tools=None: calls.pop(0)(messages, tools))

    result = AgentTurnResult()
    events = list(run_agent_turn_stream([{"role": "user", "content": "..."}], result))

    assert "done" in [e["event"] for e in events]
    tool_result = json.loads([m for m in result.new_messages if m.get("role") == "tool"][0]["content"])
    assert "error" in tool_result


def test_stream_exceeding_max_iterations_yields_error(monkeypatch):
    tool_call = LLMToolCall(id="call_1", name="search_vessel", arguments={"query": "abc"})
    always_tool_call = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    monkeypatch.setattr(
        "src.agent.agent.chat_stream", lambda messages, tools=None: _fake_stream(always_tool_call)(messages, tools)
    )

    result = AgentTurnResult()
    events = list(run_agent_turn_stream([{"role": "user", "content": "..."}], result))

    assert events[-1]["event"] == "error"
    assert str(MAX_TOOL_ITERATIONS) in events[-1]["data"]["message"]
