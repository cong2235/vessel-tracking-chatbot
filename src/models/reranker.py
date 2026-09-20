from __future__ import annotations

import httpx

from src.utils.config import (
    get_llm_timeout_seconds,
    get_openai_api_key,
    get_reranker_base_url,
    get_reranker_model,
)


def rerank(query: str, documents: list[str], top_k: int) -> list[tuple[int, float]]:
    """Tra ve [(index_trong_documents, score)] da sap xep giam dan, toi da top_k."""
    url = f"{get_reranker_base_url().rstrip('/')}/{get_reranker_model()}"
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {get_openai_api_key()}"},
        json={
            "query": query,
            "contexts": [{"text": d} for d in documents],
            "top_k": top_k,
        },
        timeout=get_llm_timeout_seconds(),
    )
    resp.raise_for_status()
    results = resp.json()["result"]["response"]
    return [(r["id"], r["score"]) for r in results]
