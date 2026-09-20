"""Unit test cho src/agent/memory.py (R3 — bộ nhớ hội thoại).

Mock đúng 2 ranh giới LLM trả phí (embed_text, chat_once dùng trong
_summarize) — DB (conversations/messages/memory_chunks, pgvector) chạy
thật, để kiểm chứng đúng logic cửa sổ/tóm tắt/truy xuất trên hạ tầng thật.
"""

from __future__ import annotations

from unittest.mock import patch

from src.agent import store
from src.agent.memory import (
    MEMORY_MIN_SIMILARITY,
    _retrieve_relevant_memory,
    _safe_window_start,
    build_llm_context,
)
from src.db import get_cursor
from src.models.llm_client import LLMResponse

DIM = 1024  # phai khop db/schema.sql: memory_chunks.embedding vector(1024)


def _unit_vector(index: int) -> list[float]:
    v = [0.0] * DIM
    v[index] = 1.0
    return v


def test_build_llm_context_returns_full_history_when_under_threshold(monkeypatch):
    monkeypatch.setenv("CONTEXT_WINDOW_TURNS", "10")
    conv = store.create_conversation()
    store.append_message(conv["id"], "user", "cau hoi 1")
    store.append_message(conv["id"], "assistant", "tra loi 1")

    with patch("src.agent.memory.embed_text") as mock_embed, patch("src.agent.memory.chat_once") as mock_chat:
        context = build_llm_context(conv["id"], "cau hoi tiep theo")

    assert len(context) == 2
    mock_embed.assert_not_called()
    mock_chat.assert_not_called()

    store.delete_conversation(conv["id"])


def test_build_llm_context_summarizes_older_messages_when_over_threshold(monkeypatch):
    monkeypatch.setenv("CONTEXT_WINDOW_TURNS", "2")
    conv = store.create_conversation()
    for i in range(5):
        store.append_message(conv["id"], "user", f"cau hoi {i}")
        store.append_message(conv["id"], "assistant", f"tra loi {i}")
    # 10 message, nguong=2 -> 8 message cu can tom tat

    fake_summary_response = LLMResponse(content="Tom tat: nguoi dung hoi 5 cau ve tau.", tool_calls=[])
    fake_embedding = _unit_vector(0)

    with patch("src.agent.memory.chat_once", return_value=fake_summary_response) as mock_chat, patch(
        "src.agent.memory.embed_text", return_value=fake_embedding
    ) as mock_embed:
        context = build_llm_context(conv["id"], "cau hoi moi nhat")

    mock_chat.assert_called_once()
    assert mock_embed.call_count == 2  # 1 lan nhung ban tom tat, 1 lan cho truy van

    # Cua so ngan han chi con 2 message gan nhat (nguong=2)
    recent_contents = [m["content"] for m in context if m["role"] in ("user", "assistant")]
    assert recent_contents[-2:] == ["cau hoi 4", "tra loi 4"]

    # Da tao dung 1 memory_chunk trong DB
    with get_cursor() as cur:
        cur.execute("SELECT count(*) AS c FROM memory_chunks WHERE conversation_id = %(cid)s", {"cid": str(conv["id"])})
        assert cur.fetchone()["c"] == 1

    store.delete_conversation(conv["id"])


def test_build_llm_context_does_not_resummarize_when_nothing_new_falls_out_of_window(monkeypatch):
    monkeypatch.setenv("CONTEXT_WINDOW_TURNS", "2")
    conv = store.create_conversation()
    for i in range(5):
        store.append_message(conv["id"], "user", f"cau hoi {i}")
        store.append_message(conv["id"], "assistant", f"tra loi {i}")

    fake_summary_response = LLMResponse(content="tom tat", tool_calls=[])
    fake_embedding = _unit_vector(0)

    with patch("src.agent.memory.chat_once", return_value=fake_summary_response) as mock_chat, patch(
        "src.agent.memory.embed_text", return_value=fake_embedding
    ):
        build_llm_context(conv["id"], "lan 1")  # trigger tom tat lan dau

    # Goi lai LAN 2 MA KHONG them message moi -> cua so khong truot them,
    # khong co message cu moi nao vua "roi" khoi cua so -> khong duoc goi
    # chat_once (tom tat) lan nua, chi duoc phep goi embed_text (truy xuat).
    with patch("src.agent.memory.chat_once") as mock_chat_2, patch(
        "src.agent.memory.embed_text", return_value=fake_embedding
    ):
        build_llm_context(conv["id"], "lan 2")

    mock_chat_2.assert_not_called()

    store.delete_conversation(conv["id"])


def test_build_llm_context_summarizes_incrementally_as_window_slides(monkeypatch):
    """Khi cua so truot toi (them message moi), cac message VUA roi khoi
    cua so ngan han phai duoc tom tat BO SUNG — khong bi bo sot, va khong
    tom tat lai nhung gi da tom tat roi."""
    monkeypatch.setenv("CONTEXT_WINDOW_TURNS", "2")
    conv = store.create_conversation()
    for i in range(5):
        store.append_message(conv["id"], "user", f"cau hoi {i}")
        store.append_message(conv["id"], "assistant", f"tra loi {i}")

    fake_summary_response = LLMResponse(content="tom tat 1", tool_calls=[])
    fake_embedding = _unit_vector(0)
    with patch("src.agent.memory.chat_once", return_value=fake_summary_response), patch(
        "src.agent.memory.embed_text", return_value=fake_embedding
    ):
        build_llm_context(conv["id"], "lan 1")  # tom tat rounds 0-3 (8 message dau)

    # Them 1 round moi -> "cau hoi 4/tra loi 4" (truoc la recent) gio bi
    # day ra khoi cua so 2-message -> can tom tat bo sung
    store.append_message(conv["id"], "user", "cau hoi 5")
    store.append_message(conv["id"], "assistant", "tra loi 5")

    fake_summary_response_2 = LLMResponse(content="tom tat 2", tool_calls=[])
    with patch("src.agent.memory.chat_once", return_value=fake_summary_response_2) as mock_chat_2, patch(
        "src.agent.memory.embed_text", return_value=fake_embedding
    ):
        build_llm_context(conv["id"], "lan 2")

    mock_chat_2.assert_called_once()
    summarized_text = mock_chat_2.call_args[0][0][1]["content"]
    assert "cau hoi 4" in summarized_text
    assert "cau hoi 0" not in summarized_text  # khong tom tat lai phan da tom tat

    with get_cursor() as cur:
        cur.execute(
            "SELECT count(*) AS c FROM memory_chunks WHERE conversation_id = %(cid)s",
            {"cid": str(conv["id"])},
        )
        assert cur.fetchone()["c"] == 2  # 2 chunk rieng biet, khong ghi de

    store.delete_conversation(conv["id"])


def test_safe_window_start_does_not_split_tool_call_pair():
    rows = [
        {"id": 1, "role": "user"},
        {"id": 2, "role": "assistant"},
        {"id": 3, "role": "assistant"},  # co tool_calls
        {"id": 4, "role": "tool"},
        {"id": 5, "role": "assistant"},
    ]
    # window_size=2 se cat vao giua row id=4 (tool) va id=5 -> phai lui ve id=3
    start = _safe_window_start(rows, window_size=2)
    assert rows[start]["id"] == 3


def test_retrieve_relevant_memory_filters_by_similarity_threshold():
    conv = store.create_conversation()
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_chunks (conversation_id, content_summary, source_msg_from_id, source_msg_to_id, embedding)
            VALUES (%(cid)s, 'lien quan', 1, 2, %(emb)s)
            """,
            {"cid": str(conv["id"]), "emb": _unit_vector(0)},
        )

    # Query giong het vector da luu -> similarity = 1.0, vuot nguong
    with patch("src.agent.memory.embed_text", return_value=_unit_vector(0)):
        results = _retrieve_relevant_memory(conv["id"], "cau hoi giong")
    assert len(results) == 1
    assert results[0]["similarity"] > MEMORY_MIN_SIMILARITY

    # Query vuong goc (orthogonal) -> similarity = 0.0, duoi nguong -> loc bo
    with patch("src.agent.memory.embed_text", return_value=_unit_vector(1)):
        results = _retrieve_relevant_memory(conv["id"], "cau hoi khac hoan toan")
    assert results == []

    store.delete_conversation(conv["id"])


def _near_aligned_vector(rank: int) -> list[float]:
    """Vector chu yeu theo huong truc 0 (giong query = _unit_vector(0)),
    cang rank cao cang lech nhieu -> similarity giam dan nhung van > 0.15,
    khac voi vector truc giao hoan toan (similarity ~ 0, bi threshold loc)."""
    v = [0.0] * DIM
    v[0] = 1.0
    v[rank + 1] = (rank + 1) * 0.3
    return v


def _insert_chunk(conv_id, summary: str, rank: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_chunks (conversation_id, content_summary, source_msg_from_id, source_msg_to_id, embedding)
            VALUES (%(cid)s, %(summary)s, 1, 2, %(emb)s)
            """,
            {"cid": str(conv_id), "summary": summary, "emb": _near_aligned_vector(rank)},
        )


def test_retrieve_relevant_memory_uses_reranker_when_enabled(monkeypatch):
    conv = store.create_conversation()
    _insert_chunk(conv["id"], "chunk A", 0)
    _insert_chunk(conv["id"], "chunk B", 1)
    _insert_chunk(conv["id"], "chunk C", 2)
    _insert_chunk(conv["id"], "chunk D", 3)

    monkeypatch.setenv("RERANKER_ENABLED", "true")
    # Reranker dua chunk D (index 3 trong danh sach candidates theo thu tu
    # tra ve tu SQL) len dau, du embedding similarity xep no thap nhat.
    fake_rerank_result = [(3, 0.99), (0, 0.5)]

    with patch("src.agent.memory.embed_text", return_value=_unit_vector(0)), patch(
        "src.agent.memory.rerank", return_value=fake_rerank_result
    ) as mock_rerank:
        results = _retrieve_relevant_memory(conv["id"], "query", top_k=2)

    mock_rerank.assert_called_once()
    assert [r["content_summary"] for r in results] == ["chunk D", "chunk A"]

    store.delete_conversation(conv["id"])


def test_retrieve_relevant_memory_falls_back_when_reranker_fails(monkeypatch):
    conv = store.create_conversation()
    _insert_chunk(conv["id"], "chunk A", 0)
    _insert_chunk(conv["id"], "chunk B", 1)
    _insert_chunk(conv["id"], "chunk C", 2)
    _insert_chunk(conv["id"], "chunk D", 3)

    monkeypatch.setenv("RERANKER_ENABLED", "true")

    with patch("src.agent.memory.embed_text", return_value=_unit_vector(0)), patch(
        "src.agent.memory.rerank", side_effect=RuntimeError("network error")
    ):
        results = _retrieve_relevant_memory(conv["id"], "query", top_k=2)

    # Khong crash - fallback ve thu tu embedding similarity, van tra ve top_k
    assert len(results) == 2

    store.delete_conversation(conv["id"])


def test_retrieve_relevant_memory_skips_reranker_when_disabled(monkeypatch):
    conv = store.create_conversation()
    _insert_chunk(conv["id"], "chunk A", 0)
    _insert_chunk(conv["id"], "chunk B", 1)

    monkeypatch.setenv("RERANKER_ENABLED", "false")

    with patch("src.agent.memory.embed_text", return_value=_unit_vector(0)), patch(
        "src.agent.memory.rerank"
    ) as mock_rerank:
        _retrieve_relevant_memory(conv["id"], "query", top_k=2)

    mock_rerank.assert_not_called()

    store.delete_conversation(conv["id"])
