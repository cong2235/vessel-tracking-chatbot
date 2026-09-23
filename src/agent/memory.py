"""Bộ nhớ hội thoại: cửa sổ ngắn hạn, tóm tắt và nhúng vào pgvector khi
vượt ngưỡng, pin fact tường minh cho yêu cầu ghi nhớ, truy xuất theo ngữ
nghĩa khi cần."""

from __future__ import annotations

import re
import unicodedata
from typing import Any
from uuid import UUID

from src.agent import store
from src.db import get_cursor
from src.models.embeddings import embed_text
from src.models.llm_client import chat_once
from src.models.reranker import rerank
from src.utils.config import get_context_window_turns, get_reranker_enabled
from src.utils.logger import get_logger

logger = get_logger(__name__)

MEMORY_RETRIEVAL_TOP_K = 3
RERANK_CANDIDATE_POOL = 20
MEMORY_MIN_SIMILARITY = 0.15

SUMMARIZE_PROMPT = (
    "Summarize (under 150 words, in English) the important information to "
    "remember from this conversation excerpt. Preserve exact numbers, "
    "names, case IDs, vessel_id, MMSI etc. verbatim. If the user asked you "
    "to 'remember' a specific piece of information (case ID, name...), you "
    "MUST list it explicitly - do not drop it in favor of other technical "
    "details (e.g. vessel specs) appearing in the same excerpt."
)

MEMORY_NOTE_PREFIX = (
    "QUAN TRONG — day la thong tin nguoi dung da yeu cau BAN GHI NHO tu "
    "truoc trong chinh hoi thoai nay. Khi nguoi dung hoi lai ve nhung gi ho "
    "da nhac/yeu cau ghi nho, PHAI dung dung thong tin duoi day, KHONG duoc "
    "nham sang chu de/tau dang noi o cac luot gan nhat:\n"
)

_REMEMBER_TRIGGER_RE = re.compile(r"ghi nho|nho giup|nho ho|hay nho|nho rang")


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_marks.replace("đ", "d").replace("Đ", "D")


def _extract_pinned_fact(row: dict[str, Any]) -> str | None:
    if row["role"] != "user" or not row["content"]:
        return None
    normalized = _strip_diacritics(row["content"]).lower()
    if _REMEMBER_TRIGGER_RE.search(normalized):
        return row["content"]
    return None


def build_llm_context(conversation_id: UUID, latest_user_message: str) -> list[dict[str, Any]]:
    window_size = get_context_window_turns()
    rows = store.list_messages(conversation_id)

    if len(rows) <= window_size:
        return [store.to_llm_message(r) for r in rows]

    start = _safe_window_start(rows, window_size)
    older_rows, recent_rows = rows[:start], rows[start:]
    _maybe_summarize_new_older_messages(conversation_id, older_rows)

    context: list[dict[str, Any]] = []
    pinned_facts = _retrieve_pinned_facts(conversation_id)
    pinned_ids = {c["id"] for c in pinned_facts}
    relevant_chunks = _retrieve_relevant_memory(conversation_id, latest_user_message)
    all_chunks = pinned_facts + [c for c in relevant_chunks if c["id"] not in pinned_ids]

    if all_chunks:
        memory_text = "\n".join(f"- {c['content_summary']}" for c in all_chunks)
        context.append({"role": "system", "content": MEMORY_NOTE_PREFIX + memory_text})
        logger.info(
            "Injected %d memory chunk(s) (%d pinned) for conversation %s: %s",
            len(all_chunks), len(pinned_facts), conversation_id,
            [c["content_summary"][:80] for c in all_chunks],
        )

    context.extend(store.to_llm_message(r) for r in recent_rows)
    return context


def _safe_window_start(rows: list[dict[str, Any]], window_size: int) -> int:
    start = max(0, len(rows) - window_size)
    while start > 0 and rows[start]["role"] == "tool":
        start -= 1
    return start


def _maybe_summarize_new_older_messages(conversation_id: UUID, older_rows: list[dict[str, Any]]) -> None:
    if not older_rows:
        return

    last_summarized_id = _get_last_summarized_message_id(conversation_id)
    new_rows = [r for r in older_rows if r["id"] > last_summarized_id]
    if not new_rows:
        return

    for row in new_rows:
        fact_text = _extract_pinned_fact(row)
        if fact_text:
            _insert_pinned_fact(conversation_id, fact_text, row["id"])

    text = _format_rows_for_summary(new_rows)
    if not text.strip():
        return

    summary = _summarize(text)
    embedding = embed_text(summary)

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_chunks
                (conversation_id, content_summary, source_msg_from_id, source_msg_to_id, embedding)
            VALUES (%(cid)s, %(summary)s, %(from_id)s, %(to_id)s, %(embedding)s)
            """,
            {
                "cid": str(conversation_id),
                "summary": summary,
                "from_id": new_rows[0]["id"],
                "to_id": new_rows[-1]["id"],
                "embedding": embedding,
            },
        )
    logger.info(
        "Summarized %d old message(s) (id %s..%s) for conversation %s",
        len(new_rows), new_rows[0]["id"], new_rows[-1]["id"], conversation_id,
    )


def _insert_pinned_fact(conversation_id: UUID, fact_text: str, source_msg_id: int) -> None:
    embedding = embed_text(fact_text)
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_chunks
                (conversation_id, content_summary, source_msg_from_id, source_msg_to_id, embedding, is_pinned)
            VALUES (%(cid)s, %(summary)s, %(mid)s, %(mid)s, %(embedding)s, true)
            """,
            {"cid": str(conversation_id), "summary": fact_text, "mid": source_msg_id, "embedding": embedding},
        )
    logger.info(
        "Pinned explicit fact for conversation %s (source msg id %s): %s",
        conversation_id, source_msg_id, fact_text[:80],
    )


def _get_last_summarized_message_id(conversation_id: UUID) -> int:
    with get_cursor() as cur:
        cur.execute(
            "SELECT max(source_msg_to_id) AS max_id FROM memory_chunks WHERE conversation_id = %(cid)s",
            {"cid": str(conversation_id)},
        )
        row = cur.fetchone()
    return row["max_id"] or 0


def _format_rows_for_summary(rows: list[dict[str, Any]]) -> str:
    lines = []
    for r in rows:
        if r["role"] == "user" and r["content"]:
            lines.append(f"User: {r['content']}")
        elif r["role"] == "assistant" and r["content"]:
            lines.append(f"Assistant: {r['content']}")
    return "\n".join(lines)


def _summarize(text: str) -> str:
    response = chat_once([{"role": "system", "content": SUMMARIZE_PROMPT}, {"role": "user", "content": text}])
    return response.content or text[:500]


def _retrieve_pinned_facts(conversation_id: UUID) -> list[dict[str, Any]]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, content_summary, source_msg_from_id, source_msg_to_id
            FROM memory_chunks
            WHERE conversation_id = %(cid)s AND is_pinned = true
            ORDER BY id
            """,
            {"cid": str(conversation_id)},
        )
        return cur.fetchall()


def _retrieve_relevant_memory(
    conversation_id: UUID, query_text: str, top_k: int = MEMORY_RETRIEVAL_TOP_K
) -> list[dict[str, Any]]:
    query_embedding = embed_text(query_text)
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, content_summary, source_msg_from_id, source_msg_to_id,
                   1 - (embedding <=> %(q)s::vector) AS similarity
            FROM memory_chunks
            WHERE conversation_id = %(cid)s AND is_pinned = false
            ORDER BY embedding <=> %(q)s::vector
            LIMIT %(pool)s
            """,
            {"cid": str(conversation_id), "q": query_embedding, "pool": RERANK_CANDIDATE_POOL},
        )
        candidates = [r for r in cur.fetchall() if r["similarity"] >= MEMORY_MIN_SIMILARITY]

    if not candidates:
        return []
    if not get_reranker_enabled() or len(candidates) <= top_k:
        return candidates[:top_k]

    try:
        ranked = rerank(query_text, [c["content_summary"] for c in candidates], top_k)
        return [candidates[i] for i, _ in ranked if i < len(candidates)]
    except Exception:
        logger.exception("Rerank failed, falling back to embedding-similarity order")
        return candidates[:top_k]
