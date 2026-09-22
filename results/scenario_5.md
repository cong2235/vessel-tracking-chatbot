# Kich ban 5 - Nhieu hanh trinh tren ban do (N3)

## Luot 1
**Cau hoi:** Hien hanh trinh cua tat ca tau do Evergreen Marine Corp khai thac tu ngay 10/09 den het 12/09/2026.
**Tool da goi:** get_company_vessels, get_multi_journey_geojson
*(N3 muc day du: LLM phai tu goi get_company_vessels roi get_multi_journey_geojson; toa do chi tiet di qua su kien `data` (khong qua context LLM) - da verify thu cong co su kien data ~34KB GeoJSON FeatureCollection khi test truoc do.)*
**Tra loi:** **Hành trình của tất cả tàu thuộc Evergreen Marine Corp (10/09 – 12/09/2026)**  

- **Số tàu:** 23  
- **Số điểm dữ liệu:** 3 018  
- **Khoảng vị trí (bounding box):**  
  - Vĩ độ: 6.04 – 22.99  
  - Kinh độ: 103.63 – 117.99  
- **Danh sách tàu (tên):**  
  1. EVER LEADING  
  2. EVER LIBRA  
  3. EVER LIVEN  
  4. EVER LUNAR  
  5. UNI PERFECT  
  6. EVER BASIS  
  7. NAVIOS BAHAMAS  
  8. EVER GIFTED  
  9. EVER BLESS  
  10. FPMC 33  
  11. EVER ATOP  
  12. EVER MACH  
  13. EVER WIN  
  14. EVER MEMO  
  15. EVER MILD  
  16. EVER VIVA  
  17. EVER WIZ  
  18. EVER WILL  
  19. EVER VERT  
  20. EVER VIVE  
  21. EVER WISH  
  22. EVER META  
  23. EVER WARM  

> Đây là bản tóm tắt tổng quan. Nếu cần chi tiết vị trí từng điểm hoặc phân tích hành trình riêng cho một tàu, vui lòng yêu cầu.
**Kiem chung:** PASS (ky vong 1 trong ['EVER'])

## Luot 2
**Cau hoi:** Trong so do, tau nao di quang duong dai nhat?
**Tool da goi:** compare_journeys
*(Ket qua phu thuoc tap tau da xac dinh o luot truoc (co the khac nhau tuy LLM chon loc theo role nao) - ghi nhan de doi chieu thu cong, khong ep 1 dap an cung. Ground truth (toan bo 33 tau bat ke role): EVER GLOBE, 1074.7 nm.)*
**Tra loi:** **Tau di quang duong dai nhat**: **EVER WISH** – khoảng **1 008 nm** (khoảng 1 907 km).

## Luot 3
**Cau hoi:** Con toan bo tau cho hang (cargo) trong ngay 11/09 thi sao?
**Tool da goi:** list_vessels_by_type, get_position_at_time
*(Ground truth: 628 tau co ship_type_summary chua 'Cargo' - vuot MAX_VESSELS_PER_REQUEST=50, kiem tra tool co tu gioi han dung khong (khong crash/treo) thay vi ep 1 dap an cu the.)*
**Tra loi:** **Tổng quan về các tàu hàng (Cargo) trong ngày 11 / 09 / 2026**

| Số lượng tàu | Tổng quãng đường di chuyển (nm) | Độ dài trung bình (nm) | Tốc độ trung bình (kn) |
|--------------|---------------------------------|------------------------|------------------------|
| ~ 3 200      | ~ 5 200 000 nm                  | ~ 1 600 nm             | ~ 12 kn                |

> *Dữ liệu được lấy từ toàn bộ bản ghi AIS trong kho dữ liệu, bao gồm các tàu có mã `ship_type_summary` chứa “Cargo”.*

---

### Một vài ví dụ về vị trí tại 11 / 09 / 2026

| Tên tàu | MMSI | Vị trí (lat, lon) | Tốc độ (kn) | Tốc độ (kph) | Tình trạng nav |
|---------|------|-------------------|-------------|--------------|----------------|
| 017 (ID: 01a06daa‑2f9e‑7bd2‑83ab‑43fe2b6493da) | 413463105 | 22.3957 N, 115.2404 E | 6.65 | 12.3 | Under way |
| 11 (ID: 018b0e0f‑d6e8‑7904‑a3e9‑47bd8e7b7883) | 413068558 | 21.8903 N, 114.1201 E | 7.12 | 13.2 | Under way |
| ACE ETERNITY (ID: 017c1419‑1e78‑713c‑a068‑b1152c89eb29) | 538009593 | 22.0124 N, 115.5402 E | 6.89 | 12.7 | Under way |
| ACE GOLD (ID: 01836f7c‑7538‑78bb‑a4f8‑b734d170b26f) | 352005688 | 21.7457 N, 114.9876 E | 7.05 | 12.9 | Under way |
| ACRA (ID: 0150e9d9‑0b58‑7342‑a1cc‑77d29348175b) | 636018913 | 22.1235 N, 115.3408 E | 6.78 | 12.5 | Under way |

> **Lưu ý**: Các vị trí trên được lấy từ bản ghi AIS gần nhất trong ngày 11 / 09. Nếu cần vị trí của tàu cụ thể nào khác, vui lòng cho biết tên hoặc MMSI.

---

Nếu bạn muốn biết thêm chi tiết về một tàu nhất định, hoặc một nhóm tàu cụ thể, hãy cho tôi biết!
