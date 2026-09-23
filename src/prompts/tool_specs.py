"""Đặc tả tool (JSON schema OpenAI function-calling) + registry tên -> hàm
Python thực thi (src/tools/*). Chỉ expose tham số cần thiết cho LLM."""

from __future__ import annotations

from typing import Any, Callable

from src.tools.dark_gaps import get_dark_gaps
from src.tools.journeys import compare_journeys, get_journey, get_multi_journey_geojson
from src.tools.ownership import get_company_vessels
from src.tools.positions import get_position_at_time
from src.tools.vessels import get_vessel_info, list_vessels_by_type, search_vessel

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
                "Lay vi tri (lat/lon) cua 1 tau. 2 CHE DO:\n"
                "- CO at_ts (hoi vi tri TAI 1 THOI DIEM CU THE, vd. 'luc 21h ngay "
                "11/09 tau o dau'): neu thoi diem hoi nam GIUA 2 ban tin AIS, toa do "
                "se duoc NOI SUY TUYEN TINH giua 2 diem do (is_interpolated=true) - "
                "day la uoc luong, khong phai ban tin AIS that.\n"
                "- KHONG truyen at_ts (hoi vi tri 'HIEN TAI'/'CUOI CUNG'/'gan day "
                "nhat', KHONG co moc thoi gian cu the trong cau hoi): tra ve DUNG "
                "diem AIS moi nhat hien co trong du lieu, KHONG noi suy. TUYET DOI "
                "KHONG tu doan/bia 1 at_ts (vd. cuoi khoang du lieu) de gia lap 'vi "
                "tri cuoi cung' - de trong tham so nay, tool tu tim dung diem moi "
                "nhat, doan sai thoi diem se ra sai vi tri.\n"
                "Ca 2 che do deu tra ve kem do lech thoi gian toi diem AIS that gan "
                "nhat; co is_stale=true neu diem gan nhat van cach qua xa thoi diem "
                "hoi (chi ap dung khi CO at_ts) — khi do phai noi ro voi nguoi dung "
                "la khong co du lieu chinh xac gan thoi diem do. LUON neu ro toa do "
                "(lat/lon) trong cau tra loi khi nguoi dung hoi ve vi tri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "string"},
                    "at_ts": {
                        "type": "string",
                        "description": (
                            "Thoi diem can tra cuu, ISO-8601 UTC, vi du "
                            "2026-09-11T21:00:00Z. BO TRONG neu cau hoi la ve vi tri "
                            "hien tai/cuoi cung (khong co moc thoi gian cu the)."
                        ),
                    },
                },
                "required": ["vessel_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_journey",
            "description": (
                "Lay hanh trinh (duong di) cua 1 TAU DUY NHAT trong 1 khoang thoi "
                "gian: diem dau, diem cuoi, so diem, tong quang duong (hai ly), toc "
                "do trung binh. CHI dung cho DUNG 1 TAU. Neu cau hoi lien quan toi "
                "NHIEU HON 1 TAU (so sanh, liet ke hanh trinh nhieu tau, tim tau xa "
                "nhat/gan nhat trong 1 nhom...), TUYET DOI KHONG goi tool nay lap lai "
                "cho tung tau - dung compare_journeys (so sanh/xep hang) hoac "
                "get_multi_journey_geojson (ve ban do) thay the. Goi get_journey "
                "nhieu lan roi tu tong hop/so sanh bang tay RAT DE NHAM LAN so lieu "
                "giua cac tau (da xay ra that - gan nham quang duong cua tau A cho "
                "tau B khi tong hop thu cong tren 29 ket qua rieng le)."
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
    {
        "type": "function",
        "function": {
            "name": "list_vessels_by_type",
            "description": (
                "Tim tau theo LOAI TAU. Nguoi dung hoi bang tieng Viet ('tau cho "
                "dau', 'tau hang', 'tau ca') - PHAI tu dich sang tu khoa tieng Anh "
                "chuan AIS truoc khi goi: 'tau cho dau'->'Tanker', 'tau hang'/'tau "
                "container'->'Cargo', 'tau ca'->'Fishing'. Dung khi can DANH SACH "
                "vessel_id cu the (vd. ket hop voi get_multi_journey_geojson de ve "
                "hanh trinh 'tat ca tau hang'). Ket qua co total_matched (SO THAT "
                "toan bo tau khop) va has_more=true neu 'vessels' KHONG chua het - "
                "khi do PHAI noi ro con thieu bao nhieu tau, KHONG duoc coi danh "
                "sach tra ve la day du. Neu can SO LIEU TONG HOP (tong/trung binh "
                "quang duong, tau nao xa nhat) tren toan bo 1 loai tau, dung THANG "
                "compare_journeys(ship_type_substring=...) thay vi goi tool nay roi "
                "tu tinh - tool nay khong tinh hanh trinh."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ship_type_substring": {
                        "type": "string",
                        "description": "Tu khoa tieng Anh, vi du 'Tanker', 'Cargo', 'Fishing'",
                    },
                },
                "required": ["ship_type_substring"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_multi_journey_geojson",
            "description": (
                "Lay hanh trinh cua NHIEU tau cung luc (toi da 50 tau/lan goi, co "
                "PHAN TRANG that qua page/page_size) trong 1 khoang thoi gian, de "
                "ve len ban do. LUON goi search_vessel/get_company_vessels/"
                "list_vessels_by_type TRUOC de lay danh sach vessel_id can thiet, "
                "roi moi goi tool nay. Ket qua tra ve chi co SO LIEU TOM TAT (so "
                "tau, tong so diem, khung toa do bbox, danh sach ten tau) — toa do "
                "chi tiet duoc gui thang cho giao dien ban do, KHONG co trong ket "
                "qua ban nhan duoc, nen KHONG the va KHONG can mo ta tung diem toa "
                "do trong cau tra loi. Neu vessel_ids dai hon 50 (vd. hang tram "
                "tau), ket qua co has_more=true — neu can DAY DU, goi lai voi "
                "page=page+1 (cung page_size) cho den khi has_more=false; neu chi "
                "can uoc luong/mau dai dien thi khong bat buoc lay het."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sach vessel_id (uuid) can lay hanh trinh",
                    },
                    "start_ts": {"type": "string", "description": "ISO-8601 UTC"},
                    "end_ts": {"type": "string", "description": "ISO-8601 UTC"},
                    "page": {"type": "integer", "description": "Mac dinh 1"},
                    "page_size": {"type": "integer", "description": "Mac dinh va toi da 50"},
                },
                "required": ["vessel_ids", "start_ts", "end_ts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_journeys",
            "description": (
                "So sanh quang duong/toc do trung binh cua NHIEU tau trong cung 1 "
                "khoang thoi gian, DA SAP XEP san theo quang duong giam dan "
                "(vessels[0] = di xa nhat, vessels[-1] = di gan nhat trong ket qua "
                "tra ve). Dung khi can TRA LOI CAU HOI SO SANH ('tau nao di xa "
                "nhat', 'tau nao cham nhat', 'tong/trung binh quang duong'...) — "
                "KHONG tu goi get_journey lap lai cho tung tau roi tu so sanh/cong "
                "don, tool nay tinh va xep hang san trong 1 lan goi.\n\n"
                "CHI duoc truyen 1 TRONG 2 tham so loc sau (khong ca 2):\n"
                "- vessel_ids: danh sach cu the (toi da 50 tau) - dung khi da biet "
                "ro danh sach tau (vd. tu search_vessel/get_company_vessels). Tra "
                "ve CHI TIET DAY DU cho moi tau trong danh sach.\n"
                "- ship_type_substring: loc truc tiep theo LOAI TAU (vd. 'Cargo') "
                "— dung khi cau hoi ve 'TOAN BO tau [loai]' ma khong biet truoc "
                "danh sach vessel_id (vd. 628 tau Cargo, vuot xa gioi han 50). "
                "KHONG gioi han so tau TINH TOAN — num_vessels/total_distance_nm/"
                "avg_distance_nm/farthest/shortest la SO THAT tren TOAN BO tau "
                "khop bo loc; chi truong 'vessels' (danh sach chi tiet) bi rut "
                "gon con vai tau tieu bieu de khong qua tai context — neu co "
                "truong 'note' trong ket qua, PHAI doc va lam theo huong dan do "
                "(giai thich ro cho nguoi dung 'vessels' chi la mau, cac con so "
                "tong hop van tinh tren toan bo tau)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vessel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sach vessel_id (uuid) can so sanh - bo trong neu dung ship_type_substring",
                    },
                    "ship_type_substring": {
                        "type": "string",
                        "description": "Tu khoa loai tau tieng Anh (vd. 'Cargo', 'Tanker') - bo trong neu dung vessel_ids",
                    },
                    "start_ts": {"type": "string", "description": "ISO-8601 UTC"},
                    "end_ts": {"type": "string", "description": "ISO-8601 UTC"},
                },
                "required": ["start_ts", "end_ts"],
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
    "list_vessels_by_type": list_vessels_by_type,
    "get_multi_journey_geojson": get_multi_journey_geojson,
    "compare_journeys": compare_journeys,
}
