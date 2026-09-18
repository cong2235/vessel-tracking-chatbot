"""Unit test cho vòng lặp tool-calling (src/agent/agent.py).

Mock chat_once để KHÔNG cần OPENAI_API_KEY / gọi LLM thật — chỉ kiểm tra
logic điều phối: gọi tool đúng tham số, đưa kết quả lại cho model, dừng
đúng lúc có câu trả lời cuối cùng, xử lý lỗi tool không làm sập vòng lặp,
và chặn được vòng lặp vô hạn.

Bản thân các tool (search_vessel, get_vessel_info...) vẫn gọi DB THẬT —
chỉ ranh giới thật sự cần mock (LLM trả phí) mới bị thay thế.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.agent.agent import MAX_TOOL_ITERATIONS, run_agent_turn
from src.models.llm_client import LLMResponse, LLMToolCall

EVER_VIVA_MMSI = "563240200"


def _assistant_message(content: str | None, tool_calls: list[LLMToolCall] | None = None) -> dict:
    msg: dict = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            }
            for tc in tool_calls
        ]
    return msg


def test_run_agent_turn_executes_real_tool_then_returns_final_answer():
    tool_call = LLMToolCall(id="call_1", name="search_vessel", arguments={"query": EVER_VIVA_MMSI})
    first_response = LLMResponse(
        content=None,
        tool_calls=[tool_call],
        raw_assistant_message=_assistant_message(None, [tool_call]),
    )
    final_response = LLMResponse(
        content="Tau EVER VIVA, MMSI 563240200.",
        tool_calls=[],
        raw_assistant_message=_assistant_message("Tau EVER VIVA, MMSI 563240200."),
    )

    with patch(
        "src.agent.agent.chat_once", side_effect=[first_response, final_response]
    ) as mock_chat:
        answer, new_messages = run_agent_turn(
            [{"role": "user", "content": "tau nao co mmsi 563240200?"}]
        )

    assert answer == "Tau EVER VIVA, MMSI 563240200."
    assert mock_chat.call_count == 2

    tool_results = [m for m in new_messages if m.get("role") == "tool"]
    assert len(tool_results) == 1
    payload = json.loads(tool_results[0]["content"])
    assert payload[0]["shipname"] == "EVER VIVA"  # tool nay goi DB that


def test_run_agent_turn_returns_immediately_when_no_tool_call():
    response = LLMResponse(
        content="Xin chao, toi giup gi duoc?",
        tool_calls=[],
        raw_assistant_message=_assistant_message("Xin chao, toi giup gi duoc?"),
    )
    with patch("src.agent.agent.chat_once", return_value=response) as mock_chat:
        answer, new_messages = run_agent_turn([{"role": "user", "content": "hi"}])

    assert answer == "Xin chao, toi giup gi duoc?"
    assert len(new_messages) == 1
    assert mock_chat.call_count == 1


def test_run_agent_turn_unknown_tool_name_returns_error_without_crashing():
    tool_call = LLMToolCall(id="call_1", name="tool_khong_ton_tai", arguments={})
    first_response = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    final_response = LLMResponse(
        content="Khong tim thay thong tin phu hop.",
        tool_calls=[],
        raw_assistant_message=_assistant_message("Khong tim thay thong tin phu hop."),
    )

    with patch("src.agent.agent.chat_once", side_effect=[first_response, final_response]):
        answer, new_messages = run_agent_turn([{"role": "user", "content": "..."}])

    tool_result = json.loads([m for m in new_messages if m.get("role") == "tool"][0]["content"])
    assert "error" in tool_result
    assert answer == "Khong tim thay thong tin phu hop."


def test_run_agent_turn_tool_exception_is_caught_and_reported_as_error():
    # vessel_id khong hop le (khong phai uuid) -> Postgres bao loi cast khi
    # chay that trong get_vessel_info -> phai duoc bat lai, khong crash loop
    tool_call = LLMToolCall(id="call_1", name="get_vessel_info", arguments={"vessel_id": "not-a-uuid"})
    first_response = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )
    final_response = LLMResponse(
        content="Da xay ra loi khi tra cuu.",
        tool_calls=[],
        raw_assistant_message=_assistant_message("Da xay ra loi khi tra cuu."),
    )

    with patch("src.agent.agent.chat_once", side_effect=[first_response, final_response]):
        answer, new_messages = run_agent_turn([{"role": "user", "content": "..."}])

    tool_result = json.loads([m for m in new_messages if m.get("role") == "tool"][0]["content"])
    assert "error" in tool_result


def test_run_agent_turn_raises_runtime_error_when_exceeding_max_iterations():
    tool_call = LLMToolCall(id="call_1", name="search_vessel", arguments={"query": "abc"})
    always_tool_call = LLMResponse(
        content=None, tool_calls=[tool_call], raw_assistant_message=_assistant_message(None, [tool_call])
    )

    with patch("src.agent.agent.chat_once", return_value=always_tool_call) as mock_chat:
        with pytest.raises(RuntimeError):
            run_agent_turn([{"role": "user", "content": "..."}])

    assert mock_chat.call_count == MAX_TOOL_ITERATIONS
