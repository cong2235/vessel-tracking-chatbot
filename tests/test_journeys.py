"""Unit test cho src/tools/journeys.py — dùng dữ liệu thật."""

from __future__ import annotations

from src.tools.journeys import get_journey, get_multi_journey_geojson

EVER_VIVA_VESSEL_ID = "01926a45-3730-7381-9acb-074f84e2e999"
KOTA_GAYA_VESSEL_ID = "014e47c3-9588-7914-9a71-4af09b458f02"


def test_get_journey_basic_stats():
    result = get_journey(
        EVER_VIVA_VESSEL_ID, "2026-09-11T00:00:00Z", "2026-09-11T23:59:59Z"
    )
    assert result["num_points"] > 0
    assert result["distance_nm"] >= 0
    assert result["geojson"] is not None
    assert result["geojson"]["type"] == "LineString"
    assert result["start_point"]["event_ts"] <= result["end_point"]["event_ts"]


def test_get_journey_avg_speed_consistent_with_distance_and_duration():
    result = get_journey(
        EVER_VIVA_VESSEL_ID, "2026-09-11T00:00:00Z", "2026-09-11T23:59:59Z"
    )
    if result["num_points"] >= 2:
        duration_hours = (
            result["end_point"]["event_ts"] - result["start_point"]["event_ts"]
        ).total_seconds() / 3600
        expected_speed = result["distance_nm"] / duration_hours if duration_hours > 0 else None
        assert result["avg_speed_knots"] == expected_speed


def test_get_journey_no_data_in_range_returns_zero():
    result = get_journey(
        EVER_VIVA_VESSEL_ID, "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"
    )
    assert result["num_points"] == 0
    assert result["distance_nm"] == 0.0
    assert result["avg_speed_knots"] is None
    assert result["geojson"] is None


def test_get_journey_unknown_vessel_returns_zero():
    result = get_journey(
        "00000000-0000-0000-0000-000000000000",
        "2026-09-10T00:00:00Z",
        "2026-09-12T23:59:59Z",
    )
    assert result["num_points"] == 0


def test_get_multi_journey_geojson_returns_one_feature_per_vessel():
    result = get_multi_journey_geojson(
        [EVER_VIVA_VESSEL_ID, KOTA_GAYA_VESSEL_ID],
        "2026-09-10T00:00:00Z",
        "2026-09-12T23:59:59Z",
    )
    assert result["num_vessels"] == 2
    assert result["total_points"] > 0
    assert len(result["bbox"]) == 4
    assert set(result["vessel_names"]) == {"EVER VIVA", "KOTA GAYA"}
    assert len(result["geojson"]["features"]) == 2
    assert all(f["geometry"]["type"] == "LineString" for f in result["geojson"]["features"])


def test_get_multi_journey_geojson_empty_list_returns_no_data():
    result = get_multi_journey_geojson([], "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z")
    assert result["num_vessels"] == 0
    assert result["geojson"] is None


def test_get_multi_journey_geojson_caps_vessel_count():
    from src.tools.journeys import MAX_VESSELS_PER_REQUEST

    too_many = [EVER_VIVA_VESSEL_ID] * (MAX_VESSELS_PER_REQUEST + 10)
    result = get_multi_journey_geojson(too_many, "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z")
    assert result["num_vessels"] <= 1  # deduped by GROUP BY vessel_id du list dai
