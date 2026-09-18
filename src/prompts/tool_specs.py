"""Đặc tả tool (JSON schema OpenAI function-calling) + registry tên -> hàm
Python thực thi (src/tools/*). Chỉ expose tham số cần thiết cho LLM."""

from __future__ import annotations

from typing import Any, Callable

from src.tools.dark_gaps import get_dark_gaps
from src.tools.journeys import get_journey
from src.tools.ownership import get_company_vessels
from src.tools.positions import get_position_at_time
from src.tools.vessels import get_vessel_info, search_vessel

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_vessel",
            "description": (
                "Tim tau theo ten, MMSI hoac IMO. Ten khong phan biet hoa/thuong va "
                "chiu duoc loi go sai nhe. LUON goi tool nay truoc khi tra loi cau "
                "hoi ve 1 tau cu the ma chua co vessel_id trong hoi thoai — KHONG tu "
                "doan vessel_id. Neu tra ve nhieu hon 1 ket qua, hoi lai nguoi dung "
                "tau nao thay vi tu chon. CHI TRA VE mmsi/imo/shipname/flag/"
                "ship_type_summary — KHONG co kich thuoc, nam dong, chu so huu, vi "
                "tri. Neu nguoi dung hoi thong tin chung chung ve 1 tau ('cho toi "
                "thong tin ve tau X'), PHAI goi tiep get_vessel_info de lay du du "
                "lieu truoc khi tra loi, khong duoc dung rieng ket qua cua tool nay."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ten tau, so MMSI (9 chu so) hoac so IMO can tim",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vessel_info",
            "description": (
                "Lay thong tin tinh day du (co, loai tau, kich thuoc, IMO...) va "
                "toan bo chu so huu/quan ly (ownership, theo tung vai tro) cua 1 "
                "tau, theo vessel_id da co tu search_vessel."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "string", "description": "vessel_id (uuid) lay tu search_vessel"},
                },
                "required": ["vessel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_vessels",
            "description": (
                "Tim cac tau lien quan toi 1 cong ty (ten cong ty co the go gan "
                "dung, se tu dong tim cac bien the ten gan giong). Dung khi nguoi "
                "dung hoi 'cong ty X con tau nao khac' hoac 'tat ca tau cua cong ty "
                "X'. Co the loc theo 1 vai tro cu the."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_query": {"type": "string", "description": "Ten cong ty can tim"},
                    "role": {
                        "type": "string",
                        "description": "Loc theo vai tro cu the (bo trong = lay tat ca vai tro)",
                        "enum": [
                            "registered_owner",
                            "beneficial_owner",
                            "operator",
                            "commercial_manager",
                            "technical_manager",
                            "ism_manager",
                        ],
                    },
                },
                "required": ["company_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_position_at_time",
            "description": (
                "Lay vi tri AIS cua 1 tau GAN 1 thoi diem cu the nhat (co the truoc "
                "hoac sau thoi diem hoi vai phut/gio, tuy ban tin AIS gan nhat). Tra "
                "ve kem do lech thoi gian va co is_stale=true neu diem gan nhat tim "
                "duoc van cach qua xa thoi diem hoi — khi do phai noi ro voi nguoi "
                "dung la khong co du lieu chinh xac gan thoi diem do."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "string"},
                    "at_ts": {
                        "type": "string",
                        "description": "Thoi diem can tra cuu, ISO-8601 UTC, vi du 2026-09-11T21:00:00Z",
                    },
                },
                "required": ["vessel_id", "at_ts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_journey",
            "description": (
                "Lay hanh trinh (duong di) cua 1 tau trong 1 khoang thoi gian: diem "
                "dau, diem cuoi, so diem, tong quang duong (hai ly), toc do trung "
                "binh."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "string"},
                    "start_ts": {"type": "string", "description": "ISO-8601 UTC"},
                    "end_ts": {"type": "string", "description": "ISO-8601 UTC"},
                },
                "required": ["vessel_id", "start_ts", "end_ts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dark_gaps",
            "description": (
                "Liet ke cac lan tau mat tin hieu AIS (dark gap, moi lan mat >= 3 "
                "gio). De hoi 'tau nao mat tin hieu lau nhat trong toan bo du lieu' "
                "thi KHONG truyen vessel_id, dung order_by='duration_desc' va "
                "limit=1. De xem toc do/vi tri NGAY TRUOC khi 1 tau cu the mat tin "
                "hieu, goi tiep get_position_at_time voi at_ts = gap_start_ts lay tu "
                "ket qua tool nay."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "string", "description": "Bo trong de tim tren toan bo du lieu"},
                    "order_by": {"type": "string", "enum": ["start_ts", "duration_desc"]},
                    "limit": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
]

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "search_vessel": search_vessel,
    "get_vessel_info": get_vessel_info,
    "get_company_vessels": get_company_vessels,
    "get_position_at_time": get_position_at_time,
    "get_journey": get_journey,
    "get_dark_gaps": get_dark_gaps,
}
