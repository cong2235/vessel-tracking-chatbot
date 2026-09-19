"""Vòng lặp tool-calling: gọi LLM -> nếu có tool_call -> chạy tool thật ->
đưa kết quả lại cho LLM -> lặp tới khi có câu trả lời cuối cùng.

run_agent_turn() (không streaming, CLI/test) và run_agent_turn_stream()
(streaming, API SSE) cố tình không hợp nhất — cơ chế đủ khác nhau (đợi
trọn phản hồi vs. xử lý từng chunk) để dùng chung dễ sinh bug hơn là lặp
code.
"""

from __future__ import annotations

import json
from typing import Any, Iterator

from src.models.llm_client import chat_once, chat_stream
from src.prompts.tool_specs import TOOL_REGISTRY, TOOL_SPECS
from src.utils.logger import get_logger

logger = get_logger(__name__)

MAX_TOOL_ITERATIONS = 8  # chan vong lap vo han neu model cu goi tool mai


def run_agent_turn(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    working_messages = list(messages)
    new_messages: list[dict[str, Any]] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = chat_once(working_messages, tools=TOOL_SPECS)

        working_messages.append(response.raw_assistant_message)
        new_messages.append(response.raw_assistant_message)

        if not response.tool_calls:
            return response.content or "", new_messages

        for tool_call in response.tool_calls:
            logger.info("tool_call name=%s args=%s", tool_call.name, tool_call.arguments)
            result = _execute_tool(tool_call.name, tool_call.arguments)
            llm_result, _geojson = _split_geojson(result)  # CLI khong co map, bo geojson
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(llm_result, default=str, ensure_ascii=False),
            }
            working_messages.append(tool_message)
            new_messages.append(tool_message)

    raise RuntimeError(
        f"Vuot qua MAX_TOOL_ITERATIONS={MAX_TOOL_ITERATIONS} ma chua co cau tra loi cuoi cung"
    )


class AgentTurnResult:
    # Generator khong tien tra ve gia tri cung luc voi yield - dung object
    # mutable de caller doc new_messages sau khi stream chay xong.
    def __init__(self) -> None:
        self.new_messages: list[dict[str, Any]] = []


def run_agent_turn_stream(
    messages: list[dict[str, Any]], result: AgentTurnResult
) -> Iterator[dict[str, Any]]:
    # Su kien: token/tool_call/done/error. Loi (LLM, vuot MAX_TOOL_ITERATIONS)
    # phat qua event error roi return, khong raise - stream SSE da mo thi
    # khong the tra HTTP error code giua chung.
    working_messages = list(messages)

    for _ in range(MAX_TOOL_ITERATIONS):
        final_response = None
        try:
            for event in chat_stream(working_messages, tools=TOOL_SPECS):
                if event["type"] == "token":
                    yield {"event": "token", "data": event["content"]}
                elif event["type"] == "final":
                    final_response = event["response"]
        except Exception as exc:
            logger.exception("Loi khi goi LLM (streaming)")
            yield {"event": "error", "data": {"message": str(exc)}}
            return

        working_messages.append(final_response.raw_assistant_message)
        result.new_messages.append(final_response.raw_assistant_message)

        if not final_response.tool_calls:
            yield {"event": "done", "data": {"answer": final_response.content or ""}}
            return

        for tool_call in final_response.tool_calls:
            logger.info("tool_call name=%s args=%s", tool_call.name, tool_call.arguments)
            yield {
                "event": "tool_call",
                "data": {"name": tool_call.name, "arguments": tool_call.arguments},
            }
            tool_result = _execute_tool(tool_call.name, tool_call.arguments)
            llm_result, geojson = _split_geojson(tool_result)
            if geojson is not None:
                yield {"event": "data", "data": {"type": "geojson", "tool": tool_call.name, "geojson": geojson}}
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(llm_result, default=str, ensure_ascii=False),
            }
            working_messages.append(tool_message)
            result.new_messages.append(tool_message)

    yield {
        "event": "error",
        "data": {"message": f"Vuot qua MAX_TOOL_ITERATIONS={MAX_TOOL_ITERATIONS}"},
    }


def _split_geojson(result: Any) -> tuple[Any, Any | None]:
    # N2/N3: tool tra ve dict co key "geojson" (co the None) -> tach rieng
    # gui cho FE ve map qua su kien `data`, khong nhet toa do tho vao
    # context LLM (chi con lai cac truong tom tat: so tau/diem/bbox...).
    if isinstance(result, dict) and "geojson" in result:
        geojson = result["geojson"]
        llm_result = {k: v for k, v in result.items() if k != "geojson"}
        return llm_result, geojson
    return result, None


def _execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    # Loi tool khong duoc thoat ra ngoai vong lap - tra ve {"error": ...}
    # de LLM biet va bao lai nguoi dung thay vi bia (R4).
    tool_fn = TOOL_REGISTRY.get(name)
    if tool_fn is None:
        return {"error": f"Tool khong ton tai: {name}"}
    try:
        return tool_fn(**arguments)
    except Exception as exc:
        logger.exception("Tool %s loi voi args=%s", name, arguments)
        return {"error": str(exc)}
