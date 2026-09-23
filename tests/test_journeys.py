"""Unit test cho src/tools/journeys.py — dùng dữ liệu thật."""

from __future__ import annotations

from src.tools.journeys import COMPARE_SAMPLE_SIZE, compare_journeys, get_journey, get_multi_journey_geojson

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
    assert result["total_vessels_requested"] == MAX_VESSELS_PER_REQUEST + 10
    assert result["has_more"] is True  # con 10 id chua duoc xu ly o trang 1


def test_get_multi_journey_geojson_pagination_covers_all_vessels_across_pages():
    all_ids = [EVER_VIVA_VESSEL_ID, KOTA_GAYA_VESSEL_ID]

    page1 = get_multi_journey_geojson(
        all_ids, "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z", page=1, page_size=1
    )
    assert page1["num_vessels"] == 1
    assert page1["has_more"] is True
    assert page1["vessel_names"] == ["EVER VIVA"]

    page2 = get_multi_journey_geojson(
        all_ids, "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z", page=2, page_size=1
    )
    assert page2["num_vessels"] == 1
    assert page2["has_more"] is False
    assert page2["vessel_names"] == ["KOTA GAYA"]

    page3 = get_multi_journey_geojson(
        all_ids, "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z", page=3, page_size=1
    )
    assert page3["num_vessels"] == 0
    assert page3["has_more"] is False


def test_compare_journeys_sorts_by_distance_descending():
    result = compare_journeys(
        [EVER_VIVA_VESSEL_ID, KOTA_GAYA_VESSEL_ID],
        "2026-09-10T00:00:00Z",
        "2026-09-12T23:59:59Z",
    )
    assert result["num_vessels"] == 2
    distances = [v["distance_nm"] for v in result["vessels"]]
    assert distances == sorted(distances, reverse=True)
    assert result["farthest"] == result["vessels"][0]
    assert result["shortest"] == result["vessels"][-1]
    assert {v["shipname"] for v in result["vessels"]} == {"EVER VIVA", "KOTA GAYA"}


def test_compare_journeys_empty_list_returns_no_data():
    result = compare_journeys([], "2026-09-10T00:00:00Z", "2026-09-12T23:59:59Z")
    assert result == {"num_vessels": 0, "vessels": [], "farthest": None, "shortest": None}


def test_compare_journeys_no_filter_returns_no_data():
    result = compare_journeys(start_ts="2026-09-10T00:00:00Z", end_ts="2026-09-12T23:59:59Z")
    assert result == {"num_vessels": 0, "vessels": [], "farthest": None, "shortest": None}


def test_compare_journeys_by_ship_type_aggregates_over_full_matching_set_not_just_sample():
    # Cargo trong data that > 50 tau (628 theo docs/architecture.md) - day
    # la case that da fail truoc: model tu bia so lieu tong hop vi khong co
    # tool nao tinh dung tren TOAN BO tau khop (chi tinh duoc tren mau hien
    # thi). Xac nhan num_vessels/total_distance_nm/avg_distance_nm tinh
    # tren DAY DU tau khop, "vessels" chi la mau (khong phai toan bo).
    result = compare_journeys(
        start_ts="2026-09-11T00:00:00Z",
        end_ts="2026-09-11T23:59:59Z",
        ship_type_substring="Cargo",
    )
    assert result["num_vessels"] > COMPARE_SAMPLE_SIZE  # nhieu hon mau hien thi
    assert len(result["vessels"]) == COMPARE_SAMPLE_SIZE
    assert result["total_distance_nm"] > 0
    assert result["avg_distance_nm"] == result["total_distance_nm"] / result["num_vessels"]
    assert result["farthest"]["distance_nm"] >= result["vessels"][0]["distance_nm"]
    assert "note" in result  # canh bao ro rang day chi la mau, tranh LLM hieu nham la toan bo


def test_compare_journeys_vessel_ids_mode_ignores_type_filter_and_returns_full_list():
    # Khi truyen vessel_ids, tra ve DAY DU (khong cat mau) va KHONG co
    # total_distance_nm/note (chi che do loc theo loai moi tra them so lieu
    # tong hop, vi vessel_ids da la danh sach day du nguoi goi chi dinh).
    result = compare_journeys(
        [EVER_VIVA_VESSEL_ID, KOTA_GAYA_VESSEL_ID],
        "2026-09-10T00:00:00Z",
        "2026-09-12T23:59:59Z",
    )
    assert len(result["vessels"]) == 2
    assert "total_distance_nm" not in result
    assert "note" not in result
