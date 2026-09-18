"""Vòng lặp tool-calling: gọi LLM -> nếu có tool_call -> chạy tool thật ->
đưa kết quả lại cho LLM -> lặp tới khi có câu trả lời cuối cùng.
"""

from __future__ import annotations

import json
from typing import Any

from src.models.llm_client import chat_once
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


def _split_geojson(result: Any) -> tuple[Any, Any | None]:
    # Khong nhet toa do tho (geojson) vao context LLM - chi con lai cac
    # truong tom tat (R4: khong dua ket qua truy van lon vao prompt).
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
