"""Unit test cho src/agent/agent.py::_split_geojson (N2/N3 — tach geojson
khoi noi dung gui cho LLM)."""

from __future__ import annotations

from src.agent.agent import _split_geojson


def test_split_geojson_extracts_and_strips_geojson_key():
    result = {"num_points": 5, "distance_nm": 10.0, "geojson": {"type": "LineString", "coordinates": []}}
    llm_result, geojson = _split_geojson(result)

    assert "geojson" not in llm_result
    assert llm_result == {"num_points": 5, "distance_nm": 10.0}
    assert geojson == {"type": "LineString", "coordinates": []}


def test_split_geojson_none_value_returns_none():
    result = {"num_points": 0, "geojson": None}
    llm_result, geojson = _split_geojson(result)

    assert llm_result == {"num_points": 0}
    assert geojson is None


def test_split_geojson_passthrough_when_no_geojson_key():
    result = {"vessel_id": "abc", "shipname": "TEST"}
    llm_result, geojson = _split_geojson(result)

    assert llm_result == result
    assert geojson is None


def test_split_geojson_passthrough_for_non_dict_result():
    result = [1, 2, 3]
    llm_result, geojson = _split_geojson(result)

    assert llm_result == result
    assert geojson is None
