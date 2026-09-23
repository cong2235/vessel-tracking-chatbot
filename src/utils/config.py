from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL chua duoc thiet lap (xem .env.example)")
    return value


def get_data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data")))


def get_log_level() -> str:
    return os.environ.get("LOG_LEVEL", "INFO").upper()


def get_openai_api_key() -> str:
    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        raise RuntimeError("OPENAI_API_KEY chua duoc thiet lap (xem .env.example)")
    return value


def get_openai_model() -> str:
    return os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def get_openai_base_url() -> str | None:
    return os.environ.get("OPENAI_BASE_URL") or None


def get_max_tokens() -> int:
    # gpt-oss dung reasoning_content (Harmony) truoc content cuoi - can du
    # token hoac content tra ve rong.
    return int(os.environ.get("LLM_MAX_TOKENS", "4096"))


def get_llm_timeout_seconds() -> float:
    # SDK mac dinh 600s - qua dai, tung treo agent vo han khi mang loi.
    return float(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))


def get_app_host() -> str:
    return os.environ.get("APP_HOST", "0.0.0.0")


def get_app_port() -> int:
    return int(os.environ.get("APP_PORT", "8000"))


def get_context_window_turns() -> int:
    return int(os.environ.get("CONTEXT_WINDOW_TURNS", "10"))


def get_embedding_model() -> str:
    return os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def get_embedding_dimensions() -> int | None:
    # Tuy chon: OpenAI text-embedding-3-* ho tro thu nho so chieu output qua
    # tham so `dimensions` (Matryoshka) ma khong can doi model - dung de giu
    # nguyen cot vector(1024) da co trong schema.sql khi doi tu bge-m3 (1024
    # chieu, khong ho tro tham so nay) sang text-embedding-3-small (mac dinh
    # 1536 chieu). Bo trong = khong truyen tham so (giu nguyen so chieu goc
    # cua model, can cho provider khong ho tro `dimensions`, vd. Cloudflare).
    value = os.environ.get("EMBEDDING_DIMENSIONS")
    return int(value) if value else None


def get_reranker_enabled() -> bool:
    return os.environ.get("RERANKER_ENABLED", "true").lower() == "true"


def get_reranker_base_url() -> str:
    value = os.environ.get("RERANKER_BASE_URL")
    if not value:
        raise RuntimeError("RERANKER_BASE_URL chua duoc thiet lap (xem .env.example)")
    return value


def get_reranker_model() -> str:
    return os.environ.get("RERANKER_MODEL", "@cf/baai/bge-reranker-base")
