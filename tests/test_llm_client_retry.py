"""Unit test cho co che retry cua src/models/llm_client.py (loi 5xx/mang
tam thoi tu LLM API — phat hien that khi chay scripts/run_scenarios.py:
1 loi 500 thoang qua tu Cloudflare lam crash ca script vi khong retry)."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, APIStatusError

from src.models.llm_client import _create_completion


def _make_status_error(status_code: int) -> APIStatusError:
    request = httpx.Request("POST", "https://example.test/chat/completions")
    response = httpx.Response(status_code, request=request)
    return APIStatusError("boom", response=response, body=None)


def test_retries_on_5xx_then_succeeds():
    client = MagicMock()
    client.chat.completions.create.side_effect = [_make_status_error(500), "ok"]

    result = _create_completion(client, model="m", messages=[])

    assert result == "ok"
    assert client.chat.completions.create.call_count == 2


def test_does_not_retry_on_4xx():
    client = MagicMock()
    client.chat.completions.create.side_effect = _make_status_error(400)

    with pytest.raises(APIStatusError):
        _create_completion(client, model="m", messages=[])

    assert client.chat.completions.create.call_count == 1


def test_retries_on_connection_error():
    client = MagicMock()
    request = httpx.Request("POST", "https://example.test/chat/completions")
    client.chat.completions.create.side_effect = [
        APIConnectionError(request=request),
        "ok",
    ]

    result = _create_completion(client, model="m", messages=[])

    assert result == "ok"
    assert client.chat.completions.create.call_count == 2


def test_gives_up_after_max_attempts():
    client = MagicMock()
    client.chat.completions.create.side_effect = _make_status_error(500)

    with pytest.raises(APIStatusError):
        _create_completion(client, model="m", messages=[])

    assert client.chat.completions.create.call_count == 3  # stop_after_attempt(3)
