"""Chuan hoa text truoc khi so khop chuoi con — dung chung giua
scripts/run_scenarios.py (check ngay trong tien trinh) va
scripts/verify_results.py (check lai offline tu file), de 2 noi khong
bao gio lech ket qua vi 1 ben chuan hoa Unicode con ben kia thi khong.

Model co the dung NBSP/narrow no-break space khi format so lieu, hoac cac
bien the dau gach ngang (en dash, em dash...) — khong phai loi noi dung.
"""

from __future__ import annotations

import re

_SPACE_CHARS = "               　"
_HYPHEN_CHARS = "‐‑‒–—"

_SPACE_RE = re.compile(f"[{_SPACE_CHARS}]")
_HYPHEN_RE = re.compile(f"[{_HYPHEN_CHARS}]")


def normalize(text: str) -> str:
    text = _SPACE_RE.sub(" ", text)
    return _HYPHEN_RE.sub("-", text)


def contains_any(haystack: str, needles: list[str]) -> list[str]:
    """Tra ve danh sach cac needle (chua chuan hoa) co xuat hien trong
    haystack sau khi chuan hoa + lower ca hai ben.

    Thu them ban "khong khoang trang" (bo het whitespace) khi so khop that
    bai - model hay dinh dang so lon co dau cach phan cach hang nghin (vd.
    "563 152 500") trong khi ground truth ky vong chuoi so lien ("563152500").
    Phat hien that tu ket qua Kich ban 1 luot 1 (MMSI)."""
    normalized = normalize(haystack).lower()
    compact = re.sub(r"\s+", "", normalized)
    matches = []
    for n in needles:
        n_norm = normalize(n).lower()
        if n_norm in normalized or re.sub(r"\s+", "", n_norm) in compact:
            matches.append(n)
    return matches
