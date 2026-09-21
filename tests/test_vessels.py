"""Unit test cho src/tools/vessels.py — chạy trên dữ liệu thật đã nạp ở
Ngày 1 (yêu cầu DATABASE_URL trỏ tới DB đã chạy scripts/load_data.py).
"""

from __future__ import annotations

from src.tools.vessels import get_vessel_info, list_vessels_by_type, search_vessel

EVER_VIVA_MMSI = 563240200
EVER_VIVA_VESSEL_ID = "01926a45-3730-7381-9acb-074f84e2e999"
EVER_VIVA_NAME = "EVER VIVA"


def test_search_vessel_by_exact_mmsi():
    results = search_vessel(str(EVER_VIVA_MMSI))
    assert len(results) == 1
    assert results[0]["vessel_id"] == EVER_VIVA_VESSEL_ID
    assert results[0]["shipname"] == EVER_VIVA_NAME


def test_search_vessel_by_name_case_insensitive():
    results = search_vessel("ever viva")
    names = [r["shipname"] for r in results]
    assert EVER_VIVA_NAME in names


def test_search_vessel_by_name_typo_uses_fuzzy_match():
    results = search_vessel("KOTA GAIA")
    names = [r["shipname"] for r in results]
    assert "KOTA GAYA" in names


def test_search_vessel_no_match_returns_empty_list():
    results = search_vessel("XYZQ_KHONG_TON_TAI_9999")
    assert results == []


def test_search_vessel_empty_query_returns_empty_list():
    assert search_vessel("") == []
    assert search_vessel("   ") == []


def test_get_vessel_info_returns_full_record_with_ownership():
    info = get_vessel_info(EVER_VIVA_VESSEL_ID)
    assert info is not None
    assert info["mmsi"] == EVER_VIVA_MMSI
    assert info["shipname"] == EVER_VIVA_NAME
    assert isinstance(info["ownership"], list)  # co the rong, nhung phai la list


def test_get_vessel_info_unknown_id_returns_none():
    assert get_vessel_info("00000000-0000-0000-0000-000000000000") is None


def test_get_vessel_info_includes_all_ownership_roles():
    # Tau nay co du 6 vai trò ownership trong data thật (xác minh thủ công)
    info = get_vessel_info("01692d7e-1ed0-7713-9c24-5e3ae1b59215")
    assert info is not None
    assert info["shipname"] == "KMTC OSAKA"
    assert len(info["ownership"]) == 6
    roles = {row["role"] for row in info["ownership"]}
    assert "registered_owner" in roles


def test_list_vessels_by_type_matches_ais_label():
    results = list_vessels_by_type("Fishing")
    assert len(results) > 0
    assert all("Fishing" in r["ship_type_summary"] for r in results)
    assert EVER_VIVA_VESSEL_ID not in [r["vessel_id"] for r in results]  # EVER VIVA la Cargo


def test_list_vessels_by_type_no_match_returns_empty():
    assert list_vessels_by_type("KhongTonTaiLoaiTauNay") == []
