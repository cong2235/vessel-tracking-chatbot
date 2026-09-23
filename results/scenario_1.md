# Kich ban 1 - Thong tin tau chu so huu va vi tri

## Luot 1
**Cau hoi:** Cho toi thong tin ve tau KOTA GAYA.
**Tool da goi:** search_vessel, get_vessel_info
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `search_vessel({"query":"KOTA GAYA"})`
   → `[{"vessel_id": "014e47c3-9588-7914-9a71-4af09b458f02", "mmsi": 563152500, "imo": "9616802", "shipname": "KOTA GAYA", "flag": "Singapore (Republic of)", "ship_type_summary": "Cargo ships, all ships of this type", "match_score": 1.0}]`
2. `get_vessel_info({"vessel_id":"014e47c3-9588-7914-9a71-4af09b458f02"})`
   → `{"vessel_id": "014e47c3-9588-7914-9a71-4af09b458f02", "mmsi": 563152500, "imo": "9616802", "shipname": "KOTA GAYA", "callsign": "9V7466", "flag_code": "SG", "flag": "Singapore (Republic of)", "ship_type_summary": "Cargo ships, all ships of this type", "ship_type_detail_name": "Container Ship", "length_m": 222.0, "width_m": 30.0, "dwt": 39598.0, "grt": 29015.0, "year_built": 2012, "ownership": [{"role": "beneficial_owner", "company_name": "PACIFIC INTERNATIONAL LINES", "company_country": "SINGAPORE", "start_date": "2011-01-25"}, {"role": "commercial_manager", "company_name": "PACIFIC INTERNATIONAL LINES", "company_country": "SINGAPORE", "start_date": "2011-01-25"}, {"role": "ism_manager", "company_name": "PACIFIC INTERNATIONAL LINES", "company_country": "SINGAPORE", "start_date": "2013-03-1...(rut gon)`

</details>
**Tra loi:** Thông tin về tàu **KOTA GAYA**:

- **MMSI**: 563152500
- **IMO**: 9616802
- **Tên tàu**: KOTA GAYA
- **Tín hiệu gọi**: 9V7466
- **Cờ**: Singapore (Cộng Hòa Singapore)
- **Loại tàu**: Tàu hàng (Container Ship)
- **Chiều dài**: 222.0 m
- **Chiều rộng**: 30.0 m
- **Trọng tải (DWT)**: 39,598 tấn
- **Tổng dung tích (GRT)**: 29,015 tấn
- **Năm chế tạo**: 2012

**Chủ sở hữu và quản lý**:
- **Công ty**: PACIFIC INTERNATIONAL LINES (Singapore)
  - Vai trò: Chủ sở hữu có lợi (Beneficial Owner) - Từ 25/01/2011
  - Vai trò: Quản lý thương mại (Commercial Manager) - Từ 25/01/2011
  - Vai trò: Quản lý ISM (ISM Manager) - Từ 13/03/2013
  - Vai trò: Điều hành (Operator) - Từ 12/11/2012
  - Vai trò: Chủ sở hữu đăng ký (Registered Owner) - Từ 17/03/2022
  - Vai trò: Quản lý kỹ thuật (Technical Manager) - Từ 13/03/2013
**Kiem chung:** PASS (ky vong noi dung 1 trong ['563152500'])

## Luot 2
**Cau hoi:** Chu so huu va cac cong ty quan ly cua tau nay la ai?
**Tra loi:** Chủ sở hữu và các công ty quản lý của tàu **KOTA GAYA** là:

- **Công ty**: PACIFIC INTERNATIONAL LINES (Singapore)
  - **Vai trò**: 
    - Chủ sở hữu có lợi (Beneficial Owner) - Từ 25/01/2011
    - Quản lý thương mại (Commercial Manager) - Từ 25/01/2011
    - Quản lý ISM (ISM Manager) - Từ 13/03/2013
    - Điều hành (Operator) - Từ 12/11/2012
    - Chủ sở hữu đăng ký (Registered Owner) - Từ 17/03/2022
    - Quản lý kỹ thuật (Technical Manager) - Từ 13/03/2013
**Kiem chung:** PASS (ky vong noi dung 1 trong ['PACIFIC INTERNATIONAL LINES'])

## Luot 3
**Cau hoi:** Cong ty chu so huu dang ky do con nhung tau nao khac trong du lieu?
**Tool da goi:** get_company_vessels
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_company_vessels({"company_query":"PACIFIC INTERNATIONAL LINES"})`
   → `{"matched_companies": [{"company_name": "PACIFIC INTERNATIONAL LINES", "match_score": 1.0}, {"company_name": "SH INTERNATIONAL LTD", "match_score": 0.44117647}], "vessels": [{"vessel_id": "014e4879-2dd0-7787-8333-072d18618487", "mmsi": 563886000, "shipname": "KOTA AZAM", "ship_type_summary": "Cargo ships, all ships of this type", "roles": ["commercial_manager", "ism_manager", "operator", "technical_manager"], "matched_company_names": ["PACIFIC INTERNATIONAL LINES"]}, {"vessel_id": "014e47c3-9588-7914-9a71-4af09b458f02", "mmsi": 563152500, "shipname": "KOTA GAYA", "ship_type_summary": "Cargo ships, all ships of this type", "roles": ["beneficial_owner", "commercial_manager", "ism_manager", "operator", "registered_owner", "technical_manager"], "matched_company_names": ["PACIFIC INTERNATIONAL ...(rut gon)`

</details>
**Tra loi:** Công ty chủ sở hữu đăng ký **PACIFIC INTERNATIONAL LINES** còn những tàu khác trong dữ liệu như sau:

1. **KOTA AZAM** (MMSI: 563886000) - Tàu hàng
2. **KOTA GAYA** (MMSI: 563152500) - Tàu hàng
3. **KOTA LAYANG** (MMSI: 563137900) - Tàu hàng (vận chuyển hàng nguy hiểm)
4. **KOTA MACHAN** (MMSI: 566894000) - Tàu hàng
5. **KOTA NAZIM** (MMSI: 565688000) - Tàu hàng
6. **KOTA NEKAD** (MMSI: 563257300) - Tàu hàng (vận chuyển hàng nguy hiểm)
7. **KOTA RATU** (MMSI: 564559000) - Tàu hàng
8. **KOTA SEGAR** (MMSI: 565357000) - Tàu hàng (vận chuyển hàng nguy hiểm)
9. **KOTA SELAMAT** (MMSI: 566282000) - Tàu hàng (vận chuyển hàng nguy hiểm)
10. **KOTA SETIA** (MMSI: 564264000) - Tàu hàng
11. **X PRESS ODYSSEY** (MMSI: 563127500) - Tàu hàng (vận chuyển hàng nguy hiểm)

Các tàu này đều nằm trong danh mục quản lý của công ty PACIFIC INTERNATIONAL LINES.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['KOTA AZAM', 'KOTA LAYANG', 'KOTA NAZIM', 'KOTA NEKAD', 'KOTA RATU', 'KOTA MACHAN', 'KOTA SEGAR', 'KOTA SELAMAT'])

## Luot 4
**Cau hoi:** Luc 21:00 ngay 11/09/2026 (UTC) tau do dang o dau?
**Tool da goi:** get_position_at_time
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_position_at_time({"vessel_id":"014e47c3-9588-7914-9a71-4af09b458f02","at_ts":"2026-09-11T21:00:00Z"})`
   → `{"vessel_id": "014e47c3-9588-7914-9a71-4af09b458f02", "event_ts": "2026-09-11T21:00:00Z", "lat": 21.745040404935146, "lon": 114.0213684024043, "speed_knots": 8.262764697209146, "course_deg": 51.0, "heading_deg": 58.0, "nav_status": "Under way", "delta_seconds": "1984.000000", "is_stale": false, "is_interpolated": true, "interpolated_between": {"before_ts": "2026-09-11 19:47:42+00:00", "after_ts": "2026-09-11 21:33:04+00:00"}}`

</details>
**Tra loi:** Lúc 21:00 ngày 11/09/2026 (UTC), tàu **KOTA GAYA** đang ở tọa độ:

- **Vĩ độ**: 21.745040
- **Kinh độ**: 114.021368

Tàu đang trong trạng thái di chuyển.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['21.74', '114.02', '21:33', '21.79', '114.08'])
