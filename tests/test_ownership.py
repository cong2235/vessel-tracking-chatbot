"""Unit test cho src/tools/ownership.py — dùng dữ liệu thật."""

from __future__ import annotations

from src.tools.ownership import get_company_vessels


def test_get_company_vessels_finds_evergreen_variants():
    result = get_company_vessels("EVERGREEN MARIN")  # co ý thiếu vài ký tự cuối
    matched_names = {row["company_name"] for row in result["matched_companies"]}

    # Data thật có it nhat 4 bien the ten cong ty Evergreen
    assert "EVERGREEN MARINE CORP" in matched_names
    assert len(matched_names) >= 2

    vessel_names = {v["shipname"] for v in result["vessels"]}
    assert len(vessel_names) > 0


def test_get_company_vessels_filters_by_role():
    result = get_company_vessels("EVERGREEN MARINE CORP", role="registered_owner")
    assert len(result["vessels"]) > 0
    assert all("registered_owner" in v["roles"] for v in result["vessels"])


def test_get_company_vessels_deduplicates_vessels_across_roles():
    # KMTC OSAKA co 6 role ownership (xac minh thu cong) - phai chi xuat
    # hien 1 lan trong danh sach tau, khong lap lai theo tung role
    result = get_company_vessels("PACIFIC INTERNATIONAL LINES")
    vessel_ids = [v["vessel_id"] for v in result["vessels"]]
    assert len(vessel_ids) == len(set(vessel_ids))


def test_get_company_vessels_no_match_returns_empty():
    result = get_company_vessels("KHONG_TON_TAI_CONG_TY_XYZ_9999")
    assert result == {"matched_companies": [], "vessels": []}


def test_get_company_vessels_empty_query_returns_empty():
    result = get_company_vessels("")
    assert result == {"matched_companies": [], "vessels": []}
