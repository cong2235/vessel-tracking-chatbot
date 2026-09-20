from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.models.reranker import rerank


def test_rerank_parses_response_into_index_score_pairs(monkeypatch):
    monkeypatch.setenv("RERANKER_BASE_URL", "https://example.test/ai/run")
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "result": {"response": [{"id": 2, "score": 0.9}, {"id": 0, "score": 0.1}]}
    }
    fake_response.raise_for_status.return_value = None

    with patch("src.models.reranker.httpx.post", return_value=fake_response) as mock_post:
        result = rerank("query", ["a", "b", "c"], top_k=2)

    assert result == [(2, 0.9), (0, 0.1)]
    assert mock_post.call_args.kwargs["json"]["query"] == "query"
    assert mock_post.call_args.kwargs["json"]["contexts"] == [{"text": "a"}, {"text": "b"}, {"text": "c"}]


def test_rerank_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("RERANKER_BASE_URL", "https://example.test/ai/run")
    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = RuntimeError("boom")

    with patch("src.models.reranker.httpx.post", return_value=fake_response):
        try:
            rerank("q", ["a"], top_k=1)
            assert False, "expected exception"
        except RuntimeError:
            pass
