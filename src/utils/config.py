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
