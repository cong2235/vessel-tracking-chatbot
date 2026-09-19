"""Lưu trữ hội thoại/tin nhắn vào Postgres (bảng conversations, messages)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg2.extras import Json

from src.db import get_cursor


def create_conversation(title: str | None = None) -> dict[str, Any]:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO conversations (title)
            VALUES (%(title)s)
            RETURNING id, title, created_at, updated_at
            """,
            {"title": title},
        )
        return cur.fetchone()


def list_conversations(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"limit": limit, "offset": offset},
        )
        return cur.fetchall()


def get_conversation(conversation_id: UUID) -> dict[str, Any] | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = %(id)s",
            {"id": str(conversation_id)},
        )
        return cur.fetchone()


def delete_conversation(conversation_id: UUID) -> bool:
    with get_cursor() as cur:
        cur.execute("DELETE FROM conversations WHERE id = %(id)s", {"id": str(conversation_id)})
        return cur.rowcount > 0


def list_messages(conversation_id: UUID) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, role, content, tool_call_id, tool_calls_json, created_at
            FROM messages
            WHERE conversation_id = %(cid)s
            ORDER BY id ASC
            """,
            {"cid": str(conversation_id)},
        )
        return cur.fetchall()


def append_message(
    conversation_id: UUID,
    role: str,
    content: str | None = None,
    tool_call_id: str | None = None,
    tool_calls_json: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (conversation_id, role, content, tool_call_id, tool_calls_json)
            VALUES (%(cid)s, %(role)s, %(content)s, %(tool_call_id)s, %(tool_calls_json)s)
            RETURNING id, role, content, tool_call_id, tool_calls_json, created_at
            """,
            {
                "cid": str(conversation_id),
                "role": role,
                "content": content,
                "tool_call_id": tool_call_id,
                "tool_calls_json": Json(tool_calls_json) if tool_calls_json is not None else None,
            },
        )
        row = cur.fetchone()
        cur.execute(
            "UPDATE conversations SET updated_at = now() WHERE id = %(cid)s",
            {"cid": str(conversation_id)},
        )
        return row


def to_llm_message(row: dict[str, Any]) -> dict[str, Any]:
    message: dict[str, Any] = {"role": row["role"], "content": row["content"]}
    if row["role"] == "assistant" and row.get("tool_calls_json"):
        message["tool_calls"] = row["tool_calls_json"]
    if row["role"] == "tool":
        message["tool_call_id"] = row["tool_call_id"]
    return message
