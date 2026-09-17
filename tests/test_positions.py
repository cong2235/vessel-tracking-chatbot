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
    assert abs(result["delta_seconds"]) <= 20 * 60  # AIS bắn tin ~15-20 phút/lần
    assert result["is_stale"] is False
    assert result["geojson"]["geometry"]["type"] == "Point"
    assert result["geojson"]["geometry"]["coordinates"] == [result["lon"], result["lat"]]


def test_get_position_at_time_far_outside_range_is_stale():
    # Ngoai het 3 ngay du lieu (10-12/09/2026) -> chac chan la stale
    result = get_position_at_time(EVER_VIVA_VESSEL_ID, "2026-01-01T00:00:00Z")
    assert result is not None
    assert result["is_stale"] is True


def test_get_position_at_time_unknown_vessel_returns_none():
    result = get_position_at_time(
        "00000000-0000-0000-0000-000000000000", "2026-09-11T12:00:00Z"
    )
    assert result is None
