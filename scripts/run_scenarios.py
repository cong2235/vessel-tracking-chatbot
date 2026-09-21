"""Chạy các kịch bản mẫu (mục 7 đề bài) qua agent THẬT (LLM thật, DB thật),
lưu transcript vào results/, và đối chiếu tự động với ground truth trong DB
để đo độ chính xác — làm cơ sở quyết định có đủ tin cậy để tiếp tục hay
không, đồng thời phục vụ D3 (bàn giao: transcript kịch bản).

Mỗi lượt có expect_any: danh sách chuỗi con — lượt PASS nếu câu trả lời
chứa ít nhất 1 chuỗi trong đó. expect_any=None: không ép pass/fail tự động
(dùng cho câu hỏi N3 mức đầy đủ, nơi tập kết quả phụ thuộc lựa chọn của LLM
ở lượt trước — chấp nhận, ghi lại để người đọc tự đánh giá thay vì áp 1 đáp
án cứng cho câu hỏi vốn mở).

Chạy:
    python scripts/run_scenarios.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ép ngưỡng nhỏ để Kịch bản 3 thực sự trigger tóm tắt + truy xuất bộ nhớ dài
# hạn (đúng gợi ý đề bài: "để người chấm giảm nhỏ khi kiểm tra"). Đặt TRƯỚC
# khi import các module đọc config lười (config đọc os.environ mỗi lần gọi
# nên set ở đây vẫn kịp).
os.environ.setdefault("CONTEXT_WINDOW_TURNS", "6")

from src.agent import store  # noqa: E402
from src.agent.agent import run_agent_turn  # noqa: E402
from src.agent.memory import build_llm_context  # noqa: E402
from src.prompts.system_prompts import SYSTEM_PROMPT  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def run_turn(conversation_id, question: str) -> tuple[str, list[str]]:
    store.append_message(conversation_id, "user", question)
    context = build_llm_context(conversation_id, question)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + context

    try:
        answer, new_messages = run_agent_turn(messages)
    except Exception as exc:
        # run_agent_turn (ban khong-streaming) raise thang thay vi phat
        # su kien error nhu ban streaming - de 1 luot loi (vd. vuot
        # MAX_TOOL_ITERATIONS khi can so sanh qua nhieu tau) khong lam mat
        # ket qua cac kich ban/luot khac trong script test nay.
        return f"[LOI: {exc}]", []

    for m in new_messages:
        if m["role"] == "assistant":
            store.append_message(
                conversation_id, "assistant", content=m.get("content"), tool_calls_json=m.get("tool_calls")
            )
        elif m["role"] == "tool":
            store.append_message(
                conversation_id, "tool", content=m.get("content"), tool_call_id=m.get("tool_call_id")
            )

    tools_called = [
        tc["function"]["name"]
        for m in new_messages
        if m.get("role") == "assistant" and m.get("tool_calls")
        for tc in m["tool_calls"]
    ]
    return answer, tools_called


def run_scenario(name: str, turns: list[dict]) -> dict:
    """turns: [{"question": str, "expect_any": list[str] | None, "note": str | None}]"""
    conv = store.create_conversation(title=name)
    records = []
    checked_count = 0
    passed_count = 0

    print(f"\n===== {name} =====")
    for i, turn in enumerate(turns, 1):
        question = turn["question"]
        expect_any = turn.get("expect_any")

        answer, tools_called = run_turn(conv["id"], question)

        passed = None
        if expect_any:
            checked_count += 1
            passed = any(exp.lower() in answer.lower() for exp in expect_any)
            if passed:
                passed_count += 1

        status = "" if passed is None else (" [OK]" if passed else " [FAIL]")
        print(f"  Luot {i}{status}: {question[:70]}")
        if tools_called:
            print(f"    tools: {tools_called}")
        if expect_any:
            print(f"    ky vong 1 trong: {expect_any} -> {'PASS' if passed else 'FAIL'}")
        print(f"    tra loi: {answer[:200]}")

        records.append(
            {
                "turn": i,
                "question": question,
                "tools_called": tools_called,
                "answer": answer,
                "expect_any": expect_any,
                "passed": passed,
                "note": turn.get("note"),
            }
        )

    store.delete_conversation(conv["id"])

    return {
        "name": name,
        "records": records,
        "checked_count": checked_count,
        "passed_count": passed_count,
    }


def write_transcript(result: dict, filename: str) -> None:
    lines = [f"# {result['name']}", ""]
    for r in result["records"]:
        lines.append(f"## Luot {r['turn']}")
        lines.append(f"**Cau hoi:** {r['question']}")
        if r["tools_called"]:
            lines.append(f"**Tool da goi:** {', '.join(r['tools_called'])}")
        if r["note"]:
            lines.append(f"*({r['note']})*")
        lines.append(f"**Tra loi:** {r['answer']}")
        if r["expect_any"] is not None:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"**Kiem chung:** {status} (ky vong 1 trong {r['expect_any']})")
        lines.append("")
    (RESULTS_DIR / filename).write_text("\n".join(lines), encoding="utf-8")


SCENARIO_1 = [
    {"question": "Cho toi thong tin ve tau KOTA GAYA.", "expect_any": ["563152500"]},
    {
        "question": "Chu so huu va cac cong ty quan ly cua tau nay la ai?",
        "expect_any": ["PACIFIC INTERNATIONAL LINES"],
    },
    {
        "question": "Cong ty chu so huu dang ky do con nhung tau nao khac trong du lieu?",
        "expect_any": [
            "KOTA AZAM", "KOTA LAYANG", "KOTA NAZIM", "KOTA NEKAD",
            "KOTA RATU", "KOTA MACHAN", "KOTA SEGAR", "KOTA SELAMAT",
        ],
    },
    {
        "question": "Luc 21:00 ngay 11/09/2026 (UTC) tau do dang o dau?",
        "expect_any": ["21:33", "21.79", "114.08"],
    },
]

SCENARIO_2 = [
    {
        "question": "Tau co MMSI 563240200 da di tu dau den dau trong ngay 11/09/2026 (UTC)?",
        "expect_any": ["447", "448"],
        "note": "ground truth: distance_nm=447.9 (Ngay 2 da xac minh)",
    },
    {
        "question": "Trong 3 ngay du lieu, tau nay co lan nao mat tin hieu AIS khong? Mat o dau va xuat hien lai o dau?",
        "expect_any": ["12/09", "12-09", "2026-09-12"],
        "note": "ground truth: gap 2026-09-12 00:14:41 -> 09:43:42",
    },
    {
        "question": "Ngay 12/09 no di duoc quang duong dai hon hay ngan hon ngay 11/09?",
        "expect_any": ["ngắn hơn", "ngan hon", "ít hơn", "it hon"],
        "note": "ground truth: day11=447.9nm > day12=213.6nm -> ngan hon",
    },
]

SCENARIO_4 = [
    {
        "question": "Tau nao mat tin hieu AIS lau nhat trong du lieu? Mat o dau va xuat hien lai o dau?",
        "expect_any": ["WORLD SPIRIT"],
        "note": "ground truth: gap_duration=229671s, dai nhat toan bo dark_gaps",
    },
    {
        "question": "Ai la chu so huu dang ky cua tau do?",
        "expect_any": ["MARIGOLD TRANSPORT"],
    },
    {
        "question": "Truoc khi mat tin hieu, tau dang chay voi toc do bao nhieu?",
        "expect_any": ["11.6", "11,6"],
    },
]


SCENARIO_5 = [
    {
        "question": (
            "Hien hanh trinh cua tat ca tau do Evergreen Marine Corp khai thac "
            "tu ngay 10/09 den het 12/09/2026."
        ),
        "expect_any": ["EVER"],
        "note": (
            "N3 muc day du: LLM phai tu goi get_company_vessels roi "
            "get_multi_journey_geojson; toa do chi tiet di qua su kien `data` "
            "(khong qua context LLM) - da verify thu cong co su kien data "
            "~34KB GeoJSON FeatureCollection khi test truoc do."
        ),
    },
    {
        "question": "Trong so do, tau nao di quang duong dai nhat?",
        "expect_any": None,
        "note": (
            "Ket qua phu thuoc tap tau da xac dinh o luot truoc (co the khac "
            "nhau tuy LLM chon loc theo role nao) - ghi nhan de doi chieu thu "
            "cong, khong ep 1 dap an cung. Ground truth (toan bo 33 tau bat ke "
            "role): EVER GLOBE, 1074.7 nm."
        ),
    },
    {
        "question": "Con toan bo tau cho hang (cargo) trong ngay 11/09 thi sao?",
        "expect_any": None,
        "note": (
            "Ground truth: 628 tau co ship_type_summary chua 'Cargo' - vuot "
            "MAX_VESSELS_PER_REQUEST=50, kiem tra tool co tu gioi han dung "
            "khong (khong crash/treo) thay vi ep 1 dap an cu the."
        ),
    },
]


def build_scenario_3() -> list[dict]:
    filler_vessels = [
        "XIANG HANG 328", "ZHU WAN 37 3", "XIN TAI HAI", "YUESHENSHANYU10016",
        "MP PREVAIL", "CHANYA NAREE", "PUSAKA PRIMA", "TS MAWEI",
        "QIONGDANYU12608", "TENGXIANHAIXIANG77",
    ]
    turns = [
        {
            "question": (
                "Ghi nho giup toi: toi phu trach ho so HS-2026-117 va dang "
                "theo doi tau MSC MANYA."
            ),
            "expect_any": None,
        }
    ]
    for name in filler_vessels:
        turns.append({"question": f"Cho toi biet loai tau va co cua tau {name}.", "expect_any": None})
    turns.append(
        {
            "question": "Ho so toi nhac tu dau cuoc tro chuyen co ma gi, va toi dang theo doi tau nao?",
            "expect_any": ["HS-2026-117"],
            "note": "kiem chung R3: nho dung sau >= 10 luot, dung ca ma ho so lan ten tau",
        }
    )
    turns.append(
        {
            "question": "Vi tri cuoi cung co trong du lieu cua tau do la o dau, luc nao?",
            "expect_any": ["18.4", "117.6", "23:50"],
            "note": "ground truth: 2026-09-12 23:50:04, lat 18.46553, lon 117.60574",
        }
    )
    return turns


def main() -> None:
    scenarios = [
        ("Kich ban 1 - Thong tin tau chu so huu va vi tri", SCENARIO_1, "scenario_1.md"),
        ("Kich ban 2 - Duong di va dark gap", SCENARIO_2, "scenario_2.md"),
        ("Kich ban 3 - Bo nho dai han vuot context window", build_scenario_3(), "scenario_3.md"),
        ("Kich ban 4 - Dark gap va tra loi khi thieu du lieu", SCENARIO_4, "scenario_4.md"),
        ("Kich ban 5 - Nhieu hanh trinh tren ban do (N3)", SCENARIO_5, "scenario_5.md"),
    ]

    total_checked = 0
    total_passed = 0
    summary = []

    for name, turns, filename in scenarios:
        result = run_scenario(name, turns)
        write_transcript(result, filename)
        total_checked += result["checked_count"]
        total_passed += result["passed_count"]
        summary.append((name, result["passed_count"], result["checked_count"]))

    print("\n===== TONG KET =====")
    for name, passed, checked in summary:
        print(f"  {name}: {passed}/{checked} kiem chung PASS")
    print(f"  TONG: {total_passed}/{total_checked} ({100 * total_passed / total_checked:.0f}%)")


if __name__ == "__main__":
    main()
