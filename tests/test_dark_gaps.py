"""Unit test cho src/tools/dark_gaps.py — dùng dữ liệu thật.

Gap dài nhất trong data (xác minh thủ công): vessel_id
014e46ee-f7d8-70c5-9b17-305e385d6ba1, gap_duration_seconds = 229671.
"""

from __future__ import annotations

import pytest

from src.tools.dark_gaps import get_dark_gaps

LONGEST_GAP_VESSEL_ID = "014e46ee-f7d8-70c5-9b17-305e385d6ba1"
LONGEST_GAP_DURATION_SECONDS = 229671


def test_get_dark_gaps_longest_overall():
    result = get_dark_gaps(order_by="duration_desc", limit=1)
    assert len(result["gaps"]) == 1
    assert result["gaps"][0]["vessel_id"] == LONGEST_GAP_VESSEL_ID
    assert result["gaps"][0]["gap_duration_seconds"] == LONGEST_GAP_DURATION_SECONDS
    assert result["geojson"]["type"] == "FeatureCollection"
    assert len(result["geojson"]["features"]) == 1


def test_get_dark_gaps_filtered_by_vessel():
    result = get_dark_gaps(vessel_id=LONGEST_GAP_VESSEL_ID)
    assert len(result["gaps"]) >= 1
    assert all(g["vessel_id"] == LONGEST_GAP_VESSEL_ID for g in result["gaps"])


def test_get_dark_gaps_unknown_vessel_returns_empty():
    result = get_dark_gaps(vessel_id="00000000-0000-0000-0000-000000000000")
    assert result["gaps"] == []
    assert result["geojson"] is None


def test_get_dark_gaps_invalid_order_by_raises():
    with pytest.raises(ValueError):
        get_dark_gaps(order_by="not_a_real_option")
