"""Wrapper gọi LLM (OpenAI Chat Completions) hỗ trợ tool-calling. Chỉ hỗ
trợ 1 nhà cung cấp — cố tình không xây abstraction đa-provider (xem
docs/research.md)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterator

from openai import APIConnectionError, APIStatusError, OpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.utils.config import (
    get_llm_timeout_seconds,
    get_max_tokens,
    get_openai_api_key,
    get_openai_base_url,
    get_openai_model,
)


def _is_retryable(exc: BaseException) -> bool:
    # 5xx/loi mang la tam thoi, dang retry. Loi 4xx (request sai) retry lai
    # cung se fail nhu vay - khong retry, tra loi ngay.
    if isinstance(exc, APIConnectionError):
        return True
    return isinstance(exc, APIStatusError) and exc.status_code >= 500


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _create_completion(client: OpenAI, **kwargs: Any) -> Any:
    return client.chat.completions.create(**kwargs)


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
        base_url = get_openai_base_url()
        if base_url is None:
            # Phat hien that: OpenAI SDK tu doc bien moi truong OPENAI_BASE_URL
            # THANG (khong qua get_openai_base_url()) khi ban trong "" van
            # con TON TAI trong os.environ (vd. dong "OPENAI_BASE_URL=" rong
            # trong .env.example/.env) - "" ton tai (khac voi bien khong ton
            # tai) khien SDK dung "" lam base_url that su, tao URL relative
            # loi "missing http(s):// protocol". Xoa han bien nay khoi
            # os.environ khi rong de SDK tu dung default that su cua no.
            os.environ.pop("OPENAI_BASE_URL", None)
        _client = OpenAI(
            api_key=get_openai_api_key(),
            base_url=base_url,
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

    response = _create_completion(client, **kwargs)
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

    stream = _create_completion(client, **kwargs)

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
