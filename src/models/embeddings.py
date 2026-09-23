"""Wrapper tạo vector embedding, dùng chung client OpenAI-compatible với
llm_client.py."""

from __future__ import annotations

from typing import Any

from src.models.llm_client import get_client
from src.utils.config import get_embedding_dimensions, get_embedding_model


def embed_text(text: str) -> list[float]:
    client = get_client()
    kwargs: dict[str, Any] = {"model": get_embedding_model(), "input": text}
    dimensions = get_embedding_dimensions()
    if dimensions:
        kwargs["dimensions"] = dimensions
    response = client.embeddings.create(**kwargs)
    return response.data[0].embedding
