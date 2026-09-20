"""Wrapper tạo vector embedding — dùng chung client OpenAI-compatible với
llm_client.py (cùng OPENAI_API_KEY/OPENAI_BASE_URL, chỉ khác model).
"""

from __future__ import annotations

from src.models.llm_client import get_client
from src.utils.config import get_embedding_model


def embed_text(text: str) -> list[float]:
    client = get_client()
    response = client.embeddings.create(model=get_embedding_model(), input=text)
    return response.data[0].embedding
