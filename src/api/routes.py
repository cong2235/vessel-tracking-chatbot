"""API quản lý hội thoại (CRUD) + chat streaming SSE (R2). Route `chat` là
`def` thường (FastAPI tự chạy trong threadpool) vì openai/psycopg2 đều
đồng bộ."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.agent import store
from src.agent.agent import AgentTurnResult, run_agent_turn_stream
from src.agent.memory import build_llm_context
from src.api.schemas import ChatRequest, ConversationCreate, ConversationOut, HealthOut, MessageOut
from src.db import get_cursor
from src.prompts.system_prompts import SYSTEM_PROMPT
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> dict[str, str]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}
    except Exception:
        logger.exception("Health check: DB khong ket noi duoc")
        return {"status": "degraded", "database": "unreachable"}


@router.post("/conversations", response_model=ConversationOut)
def create_conversation(body: ConversationCreate) -> dict[str, Any]:
    return store.create_conversation(body.title)


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    return store.list_conversations(limit=limit, offset=offset)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(conversation_id: UUID) -> list[dict[str, Any]]:
    if store.get_conversation(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Khong tim thay hoi thoai")
    return store.list_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: UUID) -> dict[str, bool]:
    deleted = store.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Khong tim thay hoi thoai")
    return {"deleted": True}


def _sse_format(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("/conversations/{conversation_id}/chat")
def chat(conversation_id: UUID, body: ChatRequest) -> StreamingResponse:
    if store.get_conversation(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Khong tim thay hoi thoai")

    store.append_message(conversation_id, "user", body.message)  # luu truoc khi goi LLM, tranh mat cau hoi neu LLM loi
    context_messages = build_llm_context(conversation_id, body.message)
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(context_messages)

    def event_generator():
        result = AgentTurnResult()
        try:
            for event in run_agent_turn_stream(messages, result):
                yield _sse_format(event["event"], event["data"])
        finally:
            _persist_new_messages(conversation_id, result.new_messages)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _persist_new_messages(conversation_id: UUID, new_messages: list[dict[str, Any]]) -> None:
    for msg in new_messages:
        if msg["role"] == "assistant":
            store.append_message(
                conversation_id,
                "assistant",
                content=msg.get("content"),
                tool_calls_json=msg.get("tool_calls"),
            )
        elif msg["role"] == "tool":
            store.append_message(
                conversation_id,
                "tool",
                content=msg.get("content"),
                tool_call_id=msg.get("tool_call_id"),
            )
        else:
            logger.warning("Bo qua message khong xac dinh role=%s khi persist", msg.get("role"))
