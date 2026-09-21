# Kich ban 1 - Thong tin tau chu so huu va vi tri

## Luot 1
**Cau hoi:** Cho toi thong tin ve tau KOTA GAYA.
**Tool da goi:** search_vessel, get_vessel_info
**Tra loi:** **Thông tin tàu KOTA GAYA**  
- **MMSI**: 563152500  
- **IMO**: 9616802  
- **Tên tàu**: KOTA GAYA  
- **Ký hiệu gọi (callsign)**: 9V7466  
- **Cờ**: Singapore (Republic of)  
- **Loại tàu**: Container Ship (Cargo)  
- **Kích thước**: 222 m chiều dài × 30 m chiều rộng  
- **Khối lượng**: 39 598 t (DWT), 29 015 t (GRT)  
- **Năm xây dựng**: 2012  

**Chủ sở hữu / Quản lý**  
- **PACIFIC INTERNATIONAL LINES** (Singapore) là:  
  - Beneficial owner (từ 2011‑01‑25)  
  - Commercial manager (từ 2011‑01‑25)  
  - ISM manager (từ 2013‑03‑13)  
  - Operator (từ 2012‑11‑12)  
  - Registered owner (từ 2022‑03‑17)  
  - Technical manager (từ 2013‑03‑13)  

**Vị trí hiện tại**: Không có dữ liệu vị trí AIS sẵn có trong hệ thống.
**Kiem chung:** PASS (ky vong 1 trong ['563152500'])

## Luot 2
**Cau hoi:** Chu so huu va cac cong ty quan ly cua tau nay la ai?
**Tra loi:** **Chủ sở hữu và các công ty quản lý của tàu KOTA GAYA:**

| Tên công ty | Quốc gia | Vai trò | Ngày bắt đầu |
|-------------|----------|--------|--------------|
| PACIFIC INTERNATIONAL LINES | Singapore | Beneficial owner | 2011‑01‑25 |
| PACIFIC INTERNATIONAL LINES | Singapore | Commercial manager | 2011‑01‑25 |
| PACIFIC INTERNATIONAL LINES | Singapore | ISM manager | 2013‑03‑13 |
| PACIFIC INTERNATIONAL LINES | Singapore | Operator | 2012‑11‑12 |
| PACIFIC INTERNATIONAL LINES | Singapore | Registered owner | 2022‑03‑17 |
| PACIFIC INTERNATIONAL LINES | Singapore | Technical manager | 2013‑03‑13 |

Vì tất cả các vai trò đều thuộc cùng một công ty PACIFIC INTERNATIONAL LINES (Singapore).
**Kiem chung:** PASS (ky vong 1 trong ['PACIFIC INTERNATIONAL LINES'])

## Luot 3
**Cau hoi:** Cong ty chu so huu dang ky do con nhung tau nao khac trong du lieu?
**Tool da goi:** get_company_vessels
**Tra loi:** **Các tàu khác mà công ty PACIFIC INTERNATIONAL LINES đăng ký là chủ sở hữu (registered_owner):**

| Tên tàu | MMSI | Loại tàu |
|---------|------|----------|
| KOTA LAYANG | 563137900 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA NAZIM | 565688000 | Cargo ships, all ships of this type |
| KOTA NEKAD | 563257300 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA RATU | 564559000 | Cargo ships, all ships of this type |
| KOTA SEGAR | 565357000 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA SELAMAT | 566282000 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category OS |
| KOTA SETIA | 564264000 | Cargo ships, all ships of this type |
| KOTA GAYA | 563152500 | Cargo ships, all ships of this type |

> **Lưu ý**: Tàu “STARSHIP AQUILA” không thuộc PACIFIC INTERNATIONAL LINES mà thuộc SH INTERNATIONAL LTD.
**Kiem chung:** FAIL (ky vong 1 trong ['KOTA AZAM', 'KOTA LAYANG', 'KOTA NAZIM', 'KOTA NEKAD', 'KOTA RATU', 'KOTA MACHAN', 'KOTA SEGAR', 'KOTA SELAMAT'])

## Luot 4
**Cau hoi:** Luc 21:00 ngay 11/09/2026 (UTC) tau do dang o dau?
**Tool da goi:** get_position_at_time
**Tra loi:** Không.  
Vào thời điểm 11/09/2026 21:00 UTC, tàu **KOTA GAYA** (MMSI 563152500) được ghi nhận đang **đang di chuyển** (nav_status = “Under way”), tốc độ khoảng 8.2 kn và hướng 58°. Vì vậy nó không ở bến / vị trí xuất phát vào thời điểm đó.
**Kiem chung:** FAIL (ky vong 1 trong ['21:33', '21.79', '114.08'])
