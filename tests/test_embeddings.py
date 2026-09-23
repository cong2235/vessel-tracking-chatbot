from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.models.embeddings import embed_text


def _fake_client_returning(vector: list[float]) -> MagicMock:
    fake_response = MagicMock()
    fake_response.data = [MagicMock(embedding=vector)]
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = fake_response
    return fake_client


def test_embed_text_passes_dimensions_when_configured(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "1024")
    fake_client = _fake_client_returning([0.1, 0.2])

    with patch("src.models.embeddings.get_client", return_value=fake_client):
        result = embed_text("hello")

    assert result == [0.1, 0.2]
    fake_client.embeddings.create.assert_called_once()
    assert fake_client.embeddings.create.call_args.kwargs["dimensions"] == 1024


def test_embed_text_omits_dimensions_when_not_configured(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIMENSIONS", raising=False)
    fake_client = _fake_client_returning([0.3])

    with patch("src.models.embeddings.get_client", return_value=fake_client):
        embed_text("hello")

    assert "dimensions" not in fake_client.embeddings.create.call_args.kwargs
