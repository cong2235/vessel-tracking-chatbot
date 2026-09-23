"""Unit test cho src/tools/positions.py — dùng dữ liệu thật.

EVER VIVA (mmsi 563240200) co ban tin AIS trong khoang
2026-09-10T20:54:42Z .. 2026-09-12T11:48:54Z (xac minh thu cong tu DB).
"""

from __future__ import annotations

from src.tools.positions import get_position_at_time

EVER_VIVA_VESSEL_ID = "01926a45-3730-7381-9acb-074f84e2e999"


def test_get_position_at_time_within_range_is_not_stale():
    result = get_position_at_time(EVER_VIVA_VESSEL_ID, "2026-09-11T12:00:00Z")
    assert result is not None
    assert abs(result["delta_seconds"]) <= 20 * 60
    assert result["is_stale"] is False
    assert result["geojson"]["geometry"]["type"] == "Point"
    assert result["geojson"]["geometry"]["coordinates"] == [result["lon"], result["lat"]]


def test_get_position_at_time_far_outside_range_is_stale():
    result = get_position_at_time(EVER_VIVA_VESSEL_ID, "2026-01-01T00:00:00Z")
    assert result is not None
    assert result["is_stale"] is True


def test_get_position_at_time_unknown_vessel_returns_none():
    result = get_position_at_time(
        "00000000-0000-0000-0000-000000000000", "2026-09-11T12:00:00Z"
    )
    assert result is None


def test_get_position_at_time_interpolates_between_two_real_points():
    result = get_position_at_time(EVER_VIVA_VESSEL_ID, "2026-09-11T12:20:00Z")
    assert result is not None
    assert result["is_interpolated"] is True
    assert result["is_stale"] is False
    assert 9.6735 < result["lat"] < 9.93066
    assert 109.30558 < result["lon"] < 109.46918
    assert "interpolated_between" in result
    assert result["interpolated_between"]["before_ts"].startswith("2026-09-11 11:50:35")
    assert result["interpolated_between"]["after_ts"].startswith("2026-09-11 12:49:37")


def test_get_position_at_time_exact_match_is_not_interpolated():
    result = get_position_at_time(EVER_VIVA_VESSEL_ID, "2026-09-11T11:50:35Z")
    assert result is not None
    assert result["is_interpolated"] is False
    assert result["delta_seconds"] == 0
    assert abs(result["lat"] - 9.6735) < 1e-6


def test_get_position_at_time_no_at_ts_returns_latest_point_not_earliest():
    result = get_position_at_time(EVER_VIVA_VESSEL_ID)
    assert result is not None
    assert result["event_ts"].startswith("2026-09-12 11:48:54")
    assert result["is_interpolated"] is False
    assert result["is_stale"] is False


def test_get_position_at_time_no_at_ts_unknown_vessel_returns_none():
    result = get_position_at_time("00000000-0000-0000-0000-000000000000")
    assert result is None
