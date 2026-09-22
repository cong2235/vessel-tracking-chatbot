"""Unit test cho src/utils/text_normalize.py — dung chung giua
scripts/run_scenarios.py va scripts/verify_results.py."""

from __future__ import annotations

from src.utils.text_normalize import contains_any, normalize


def test_normalize_converts_unicode_space_variants_to_ascii_space():
    assert normalize("563 152 500") == "563 152 500"
    assert normalize("2026‐09‐12") == "2026-09-12"


def test_contains_any_matches_exact_substring():
    assert contains_any("Tau EVER VIVA co MMSI 563240200", ["563240200"]) == ["563240200"]


def test_contains_any_matches_across_thousand_separator_spaces():
    # Phat hien that tu Kich ban 1 luot 1: model dinh dang "563 152 500"
    # (dau cach ASCII thuong, khong phai Unicode dac biet) trong khi ground
    # truth ky vong chuoi so lien "563152500" - phai van khop.
    assert contains_any("MMSI: 563 152 500", ["563152500"]) == ["563152500"]


def test_contains_any_returns_empty_when_no_match():
    assert contains_any("khong lien quan", ["563152500"]) == []


def test_contains_any_returns_all_matching_needles():
    matched = contains_any("ngan hon truoc do", ["ngắn hơn", "ngan hon", "dai hon"])
    assert matched == ["ngan hon"]
