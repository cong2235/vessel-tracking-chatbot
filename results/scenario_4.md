# Kich ban 4 - Dark gap va tra loi khi thieu du lieu

## Luot 1
**Cau hoi:** Tau nao mat tin hieu AIS lau nhat trong du lieu? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps, get_position_at_time, get_position_at_time
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_dark_gaps({"order_by":"duration_desc","limit":1})`
   → `{"gaps": [{"gap_id": "01a09659-c260-74a5-85a1-e0a92a410fbd", "vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "shipname": "WORLD SPIRIT", "gap_start_ts": "2026-09-10 00:13:09+00:00", "gap_end_ts": "2026-09-12 16:01:00+00:00", "gap_duration_seconds": 229671, "distance_nm": 68.679798314168, "implied_speed_knots": 1.0765280506942747, "start_lat": 9.066532135009766, "start_lon": 102.82848358154297, "end_lat": 8.53100872039795, "end_lon": 103.851318359375}]}`
2. `get_position_at_time({"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "at_ts": "2026-09-10 00:13:09+00:00"})`
   → `{"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "event_ts": "2026-09-10 00:13:09+00:00", "lat": 9.06653, "lon": 102.82848, "speed_knots": 11.600000381469727, "course_deg": 336.0, "heading_deg": null, "nav_status": "Under way", "delta_seconds": "0.000000", "is_stale": false, "is_interpolated": false}`
3. `get_position_at_time({"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "at_ts": "2026-09-12 16:01:00+00:00"})`
   → `{"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "event_ts": "2026-09-12 16:01:00+00:00", "lat": 8.53101, "lon": 103.85132, "speed_knots": 15.5, "course_deg": 119.0, "heading_deg": 122.0, "nav_status": "Under way", "delta_seconds": "0.000000", "is_stale": false, "is_interpolated": false}`

</details>
*(ground truth: gap_duration=229671s, dai nhat toan bo dark_gaps)*
**Tra loi:** Tau mat tin hieu AIS lau nhat là **WORLD SPIRIT**. 

- Mốc thời gian bắt đầu mất tín hiệu: **00:13:09, ngày 10 tháng 9 năm 2026** tại tọa độ:
  - Vĩ độ: **9.06653**
  - Kinh độ: **102.82848**

- Mốc thời gian xuất hiện lại: **16:01:00, ngày 12 tháng 9 năm 2026** tại tọa độ:
  - Vĩ độ: **8.53101**
  - Kinh độ: **103.85132**

Tọa độ ban đầu khi mất tín hiệu nằm gần bờ biển Thái Lan, và tọa độ xuất hiện lại nằm gần bờ biển Malaysia.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['WORLD SPIRIT'])

## Luot 2
**Cau hoi:** Ai la chu so huu dang ky cua tau do?
**Tool da goi:** get_vessel_info
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_vessel_info({"vessel_id":"014e46ee-f7d8-70c5-9b17-305e385d6ba1"})`
   → `{"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "mmsi": 636011023, "imo": "9175925", "shipname": "WORLD SPIRIT", "callsign": "ELWG7", "flag_code": "LR", "flag": "Liberia (Republic of)", "ship_type_summary": "Cargo ships, all ships of this type", "ship_type_detail_name": "Vehicles Carrier", "length_m": 174.98, "width_m": 29.200001, "dwt": 14101.0, "grt": 37949.0, "year_built": 1998, "ownership": [{"role": "beneficial_owner", "company_name": "MITSUI OSK LINES LTD", "company_country": "JAPAN", "start_date": "2001-02-23"}, {"role": "commercial_manager", "company_name": "FAIRMONT SHIPPING HK LTD", "company_country": "HONG KONG", "start_date": "2023-11-11"}, {"role": "ism_manager", "company_name": "FAIRMONT SHIPPING HK LTD", "company_country": "HONG KONG", "start_date": "2023-11-11"}, {"ro...(rut gon)`

</details>
**Tra loi:** Chủ sở hữu đăng ký của tàu **WORLD SPIRIT** là **MARIGOLD TRANSPORT INC**, có trụ sở tại **Liberia**.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['MARIGOLD TRANSPORT'])

## Luot 3
**Cau hoi:** Truoc khi mat tin hieu, tau dang chay voi toc do bao nhieu?
**Tool da goi:** get_position_at_time
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_position_at_time({"vessel_id":"014e46ee-f7d8-70c5-9b17-305e385d6ba1","at_ts":"2026-09-10T00:13:09Z"})`
   → `{"vessel_id": "014e46ee-f7d8-70c5-9b17-305e385d6ba1", "event_ts": "2026-09-10 00:13:09+00:00", "lat": 9.06653, "lon": 102.82848, "speed_knots": 11.600000381469727, "course_deg": 336.0, "heading_deg": null, "nav_status": "Under way", "delta_seconds": "0.000000", "is_stale": false, "is_interpolated": false}`

</details>
**Tra loi:** Trước khi mất tín hiệu, tàu **WORLD SPIRIT** đang chạy với tốc độ **11.6 knots**.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['11.6', '11,6'])
