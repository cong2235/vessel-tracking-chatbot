"""Wrapper tạo vector embedding — dùng chung client OpenAI-compatible với
llm_client.py (cùng OPENAI_API_KEY/OPENAI_BASE_URL, chỉ khác model).
"""

from __future__ import annotations

from typing import Any

from src.models.llm_client import get_client
from src.utils.config import get_embedding_dimensions, get_embedding_model


def embed_text(text: str) -> list[float]:
    client = get_client()
    kwargs: dict[str, Any] = {"model": get_embedding_model(), "input": text}
    dimensions = get_embedding_dimensions()
    if dimensions:
        # Chi OpenAI text-embedding-3-* ho tro tham so nay (Matryoshka) - de
        # trong (mac dinh None) khi dung provider khac (vd. Cloudflare bge-m3)
        # vi ho co the tra loi 400 voi tham so la.
        kwargs["dimensions"] = dimensions
    response = client.embeddings.create(**kwargs)
    return response.data[0].embedding
