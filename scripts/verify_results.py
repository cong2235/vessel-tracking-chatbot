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

from src.utils.text_normalize import contains_any, normalize

RESULTS_DIR = PROJECT_ROOT / "results"

CHECKS: dict[str, list[tuple[int, list[str] | None, list[str] | None]]] = {
    "scenario_1.md": [
        (1, ["563152500"], None),
        (2, ["PACIFIC INTERNATIONAL LINES"], None),
        (3, ["KOTA AZAM", "KOTA LAYANG", "KOTA NAZIM", "KOTA NEKAD", "KOTA RATU", "KOTA MACHAN", "KOTA SEGAR", "KOTA SELAMAT"], None),
        (4, ["21.74", "114.02", "21:33", "21.79", "114.08"], None),
    ],
    "scenario_2.md": [
        (1, ["447", "448"], None),
        (2, ["12/09", "12-09", "2026-09-12"], None),
        (3, ["ngắn hơn", "ngan hon", "ít hơn", "it hon", "dài hơn", "dai hon"], None),
    ],
    "scenario_3.md": [
        (12, ["HS-2026-117"], None),
        (13, ["18.4", "117.6", "23:50"], None),
    ],
    "scenario_4.md": [
        (1, ["WORLD SPIRIT"], None),
        (2, ["MARIGOLD TRANSPORT"], None),
        (3, ["11.6", "11,6"], None),
    ],
    "scenario_5.md": [
        (1, ["EVER"], None),
        (2, None, ["compare_journeys"]),
        (3, None, ["compare_journeys"]),
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
        for turn_no, expect_any, expect_tool in checks:
            marker = f"## luot {turn_no}\n"
            start = content.find(marker)
            end = content.find("\n## luot ", start + 1)
            section = content[start:end if end != -1 else len(content)]

            answer_start = section.find("**tra loi:**")
            answer_end = section.find("**kiem chung:**")
            answer_section = section[
                answer_start if answer_start != -1 else 0 : answer_end if answer_end != -1 else len(section)
            ]
            tool_line_start = section.find("**tool da goi:**")
            tool_line_end = section.find("\n", tool_line_start) if tool_line_start != -1 else -1
            tool_line = section[tool_line_start:tool_line_end] if tool_line_start != -1 else ""

            total_checked += 1
            text_matched = contains_any(answer_section, expect_any) if expect_any else None
            tool_matched = contains_any(tool_line, expect_tool) if expect_tool else None
            passed = bool((expect_any is None or text_matched) and (expect_tool is None or tool_matched))
            if passed:
                total_passed += 1
            status = "PASS" if passed else "FAIL"
            detail_parts = []
            if expect_any:
                detail_parts.append(f"noi dung khop: {text_matched or 'KHONG CO'}")
            if expect_tool:
                detail_parts.append(f"tool khop: {tool_matched or 'KHONG CO'}")
            out_lines.append(f"  Luot {turn_no}: {status} ({'; '.join(detail_parts)})")

    out_lines.append(f"\nTONG: {total_passed}/{total_checked} ({100 * total_passed / total_checked:.0f}%)")

    report = "\n".join(out_lines)
    (PROJECT_ROOT / "results" / "verify_summary.txt").write_text(report, encoding="utf-8")
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
