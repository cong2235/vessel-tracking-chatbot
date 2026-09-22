# Kich ban 1 - Thong tin tau chu so huu va vi tri

## Luot 1
**Cau hoi:** Cho toi thong tin ve tau KOTA GAYA.
**Tool da goi:** search_vessel
**Tra loi:** **Thông tin tàu KOTA GAYA**

| Tên tàu | MMSI | IMO | Quốc hiệu | Loại tàu |
|---------|-------|-----|------------|----------|
| KOTA GAYA | 563 152 500 | 9616802 | Singapore (Republic of) | Cargo ships (all ships of this type) |

Không có dữ liệu về chủ sở hữu, vị trí hiện tại hay lịch trình trong hệ thống.
**Kiem chung:** FAIL (ky vong 1 trong ['563152500'])

## Luot 2
**Cau hoi:** Chu so huu va cac cong ty quan ly cua tau nay la ai?
**Tool da goi:** get_vessel_info
**Tra loi:** **Chu sở vụ và các công ty quản lý của tàu KOTA GAYA**

- **Beneficial Owner**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 25 tháng 1 2011  
- **Commercial Manager**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 25 tháng 1 2011  
- **ISM Manager**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 13 tháng 3 2013  
- **Operator**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 12 tháng 11 2012  
- **Registered Owner**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 17 tháng 3 2022  
- **Technical Manager**: PACIFIC INTERNATIONAL LINES (Singapore) – bắt đầu từ 13 tháng 3 2013
**Kiem chung:** PASS (ky vong 1 trong ['PACIFIC INTERNATIONAL LINES'])

## Luot 3
**Cau hoi:** Cong ty chu so huu dang ky do con nhung tau nao khac trong du lieu?
**Tool da goi:** get_company_vessels
**Tra loi:** **Các tàu khác được đăng ký bởi công ty PACIFIC INTERNATIONAL LINES (vai trò registered_owner):**

| Tên tàu | MMSI | Loại tàu |
|--------|------|----------|
| KOTA LAYANG | 563 137 900 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA NAZIM | 565 688 000 | Cargo ships, all ships of this type |
| KOTA NEKAD | 563 257 300 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA RATU | 564 559 000 | Cargo ships, all ships of this type |
| KOTA SEGAR | 565 357 000 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X |
| KOTA SELAMAT | 566 282 000 | Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category OS |
| KOTA SETIA | 564 264 000 | Cargo ships, all ships of this type |

> *Dữ liệu lấy từ kết quả hàm `get_company_vessels` với `company_query = "PACIFIC INTERNATIONAL LINES"` và `role = "registered_owner"`.*
**Kiem chung:** PASS (ky vong 1 trong ['KOTA AZAM', 'KOTA LAYANG', 'KOTA NAZIM', 'KOTA NEKAD', 'KOTA RATU', 'KOTA MACHAN', 'KOTA SEGAR', 'KOTA SELAMAT'])

## Luot 4
**Cau hoi:** Luc 21:00 ngay 11/09/2026 (UTC) tau do dang o dau?
**Tool da goi:** get_position_at_time
**Tra loi:** Không, tại 21:00 UTC ngày 11/09/2026 tàu **KOTA GAYA** không đang neo.  
- **Vị trí ước tính**: 21.7450 N, 114.0214 E.  
- **Trạng thái**: “Under way” (đang di chuyển).  
- Điểm dữ liệu là dữ liệu *được nội suy* giữa hai bản tin AIS gần nhất, vì vậy không phải là bản tin thực tế.
**Kiem chung:** FAIL (ky vong 1 trong ['21:33', '21.79', '114.08'])
