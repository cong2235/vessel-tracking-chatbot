"""Wrapper gọi LLM (OpenAI Chat Completions) hỗ trợ tool-calling. Chỉ hỗ
trợ 1 nhà cung cấp — cố tình không xây abstraction đa-provider (xem
docs/research.md)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterator

from openai import OpenAI

from src.utils.config import (
    get_llm_timeout_seconds,
    get_max_tokens,
    get_openai_api_key,
    get_openai_base_url,
    get_openai_model,
)


@dataclass
class LLMToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    raw_assistant_message: dict[str, Any] = field(default_factory=dict)


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=get_openai_api_key(),
            base_url=get_openai_base_url(),
            timeout=get_llm_timeout_seconds(),  # SDK mac dinh 600s, qua dai
        )
    return _client


def chat_once(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> LLMResponse:
    client = get_client()

    kwargs: dict[str, Any] = {
        "model": get_openai_model(),
        "messages": messages,
        "max_tokens": get_max_tokens(),
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    # content=None (tool_calls-only) hop le theo OpenAI nhung mot so API
    # tuong thich (vd. Cloudflare) tra 400 - dung "" cho message gui di.
    assistant_message: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
    tool_calls: list[LLMToolCall] = []

    if message.tool_calls:
        assistant_message["tool_calls"] = []
        for tc in message.tool_calls:
            assistant_message["tool_calls"].append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
            )
            tool_calls.append(
                LLMToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments or "{}"),
                )
            )

    return LLMResponse(
        content=message.content,
        tool_calls=tool_calls,
        raw_assistant_message=assistant_message,
    )


def chat_stream(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> Iterator[dict[str, Any]]:
    # Yield {"type":"token","content":...}* roi {"type":"final","response":LLMResponse}.
    # tool_calls stream theo tung manh arguments (cung 1 index) - phai gop
    # lai roi moi parse JSON duoc.
    client = get_client()

    kwargs: dict[str, Any] = {
        "model": get_openai_model(),
        "messages": messages,
        "stream": True,
        "max_tokens": get_max_tokens(),
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    stream = client.chat.completions.create(**kwargs)

    content_parts: list[str] = []
    tool_call_buffers: dict[int, dict[str, str | None]] = {}

    for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.content:
            content_parts.append(delta.content)
            yield {"type": "token", "content": delta.content}

        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                buf = tool_call_buffers.setdefault(
                    tc_delta.index, {"id": None, "name": None, "arguments": ""}
                )
                if tc_delta.id:
                    buf["id"] = tc_delta.id
                if tc_delta.function and tc_delta.function.name:
                    buf["name"] = tc_delta.function.name
                if tc_delta.function and tc_delta.function.arguments:
                    buf["arguments"] = (buf["arguments"] or "") + tc_delta.function.arguments

    full_content = "".join(content_parts) or None
    assistant_message: dict[str, Any] = {"role": "assistant", "content": full_content or ""}
    tool_calls: list[LLMToolCall] = []

    if tool_call_buffers:
        assistant_message["tool_calls"] = []
        for index in sorted(tool_call_buffers):
            buf = tool_call_buffers[index]
            assistant_message["tool_calls"].append(
                {
                    "id": buf["id"],
                    "type": "function",
                    "function": {"name": buf["name"], "arguments": buf["arguments"]},
                }
            )
            tool_calls.append(
                LLMToolCall(
                    id=buf["id"],
                    name=buf["name"],
                    arguments=json.loads(buf["arguments"] or "{}"),
                )
            )

    yield {
        "type": "final",
        "response": LLMResponse(
            content=full_content,
            tool_calls=tool_calls,
            raw_assistant_message=assistant_message,
        ),
    }
