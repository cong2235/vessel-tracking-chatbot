"""Kết nối PostgreSQL dùng chung."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

from src.utils.config import get_database_url


@contextmanager
def get_cursor() -> Iterator[psycopg2.extras.RealDictCursor]:
    conn = psycopg2.connect(get_database_url())
    register_vector(conn)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
