"""Kiểm chứng LẠI (offline, đọc file) kết quả các kịch bản đã lưu trong
results/*.md — tách biệt hoàn toàn khỏi quá trình sinh dữ liệu
(scripts/run_scenarios.py) để tránh mọi bất thường runtime khi kiểm tra
trực tiếp trong tiến trình đang gọi LLM.

Dùng chung src/utils/text_normalize.py với run_scenarios.py — trước đây 2
script tự định nghĩa 2 hàm chuẩn hoá khác nhau nên có thể ra kết quả PASS/
FAIL lệch nhau cho cùng 1 lượt (vd. scenario_1.md lượt 3, phát hiện khi
soát lại kết quả); giờ chỉ còn 1 nguồn logic duy nhất.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.text_normalize import contains_any, normalize  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results"

CHECKS: dict[str, list[tuple[int, list[str]]]] = {
    "scenario_1.md": [
        (1, ["563152500"]),
        (2, ["PACIFIC INTERNATIONAL LINES"]),
        (3, ["KOTA AZAM", "KOTA LAYANG", "KOTA NAZIM", "KOTA NEKAD", "KOTA RATU", "KOTA MACHAN", "KOTA SEGAR", "KOTA SELAMAT"]),
        # Nhan noi suy tuyen tinh (item #7) - vi tri that luc 21:00 nam giua
        # 2 ban tin AIS (19:47 va 21:33) nen ket qua dung la toa do noi suy
        # (21.7450, 114.0214), khong phai toa do ban tin gan nhat (21.79,
        # 114.08) nhu truoc khi co noi suy - chap nhan ca 2 dang tra loi.
        (4, ["21.74", "114.02", "21:33", "21.79", "114.08"]),
    ],
    "scenario_2.md": [
        (1, ["447", "448"]),
        (2, ["12/09", "12-09", "2026-09-12"]),
        # Chap nhan ca 2 dien dat tuong duong: "ngay 12 ngan hon" hoac "ngay
        # 11 dai hon" (cung 1 su that 447>213nm) - xem run_scenarios.py.
        (3, ["ngắn hơn", "ngan hon", "ít hơn", "it hon", "dài hơn", "dai hon"]),
    ],
    "scenario_3.md": [
        (12, ["HS-2026-117"]),
        (13, ["18.4", "117.6", "23:50"]),
    ],
    "scenario_4.md": [
        (1, ["WORLD SPIRIT"]),
        (2, ["MARIGOLD TRANSPORT"]),
        (3, ["11.6", "11,6"]),
    ],
    "scenario_5.md": [
        (1, ["EVER"]),
    ],
}


def main() -> None:
    total_checked = 0
    total_passed = 0
    out_lines: list[str] = []

    for filename, checks in CHECKS.items():
        path = RESULTS_DIR / filename
        if not path.exists():
            out_lines.append(f"[SKIP] {filename} khong ton tai")
            continue
        content = normalize(path.read_text(encoding="utf-8")).lower()

        out_lines.append(f"\n=== {filename} ===")
        for turn_no, expect_any in checks:
            marker = f"## luot {turn_no}\n"
            start = content.find(marker)
            end = content.find("\n## luot ", start + 1)
            section = content[start:end if end != -1 else len(content)]

            # QUAN TRONG: chi kiem tra trong phan "**tra loi:**" — section
            # con chua ca dong "**kiem chung:** FAIL (ky vong 1 trong
            # [...])" tu lan chay truoc, dong nay LAP LAI chinh chuoi ky
            # vong nen se tu khop nham voi chinh no (khong phai voi cau tra
            # loi that cua model) neu khong cat bo.
            answer_start = section.find("**tra loi:**")
            answer_end = section.find("**kiem chung:**")
            answer_section = section[
                answer_start if answer_start != -1 else 0 : answer_end if answer_end != -1 else len(section)
            ]

            total_checked += 1
            matched = contains_any(answer_section, expect_any)
            passed = bool(matched)
            if passed:
                total_passed += 1
            status = "PASS" if passed else "FAIL"
            out_lines.append(f"  Luot {turn_no}: {status} (khop: {matched if matched else 'KHONG CO'})")

    out_lines.append(f"\nTONG: {total_passed}/{total_checked} ({100 * total_passed / total_checked:.0f}%)")

    report = "\n".join(out_lines)
    (PROJECT_ROOT / "results" / "verify_summary.txt").write_text(report, encoding="utf-8")
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
