"""Unit test cho co che retry cua src/models/llm_client.py"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, APIStatusError

import src.models.llm_client as llm_client_module
from src.models.llm_client import _create_completion, get_client


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


def test_get_client_ignores_empty_string_base_url_env_var(monkeypatch):
    # Phat hien that: neu OPENAI_BASE_URL="" TON TAI trong os.environ (vd.
    # dong "OPENAI_BASE_URL=" rong con lai trong .env, dung theo huong dan
    # cua .env.example), OpenAI SDK tu doc thang bien nay va dung "" lam
    # base_url that su -> tao URL relative, loi "missing http(s)://
    # protocol" khi goi that (khong lien quan gi den get_openai_base_url()
    # cua ta, von da xu ly dung "" -> None). get_client() phai xoa han bien
    # rong nay khoi os.environ truoc khi tao client de SDK tu dung dung
    # default cua no.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setattr(llm_client_module, "_client", None)
    try:
        client = get_client()
        assert str(client.base_url).startswith("https://api.openai.com")
    finally:
        monkeypatch.setattr(llm_client_module, "_client", None)
