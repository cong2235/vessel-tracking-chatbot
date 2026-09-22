# Kich ban 2 - Duong di va dark gap

## Luot 1
**Cau hoi:** Tau co MMSI 563240200 da di tu dau den dau trong ngay 11/09/2026 (UTC)?
**Tool da goi:** search_vessel, get_journey
*(ground truth: distance_nm=447.9 (Ngay 2 da xac minh))*
**Tra loi:** Vâng, tau MMSI 563 240 200 (tên EVER VIVA) đã đi từ một cảng đến một cảng trong ngày 11/09/2026 (UTC).

**Chi tiết hành trình:**

| Thời điểm | Vị trí (lat/lon) | Tốc độ | Ghi chú |
|-----------|------------------|--------|---------|
| 2026‑09‑11 00:00 UTC | 6.80919 N, 106.98844 E | 17.9 kt | Khởi hành từ cảng Jakarta (Indonesia) |
| 2026‑09‑11 23:53 23 UTC | 12.9847 N, 111.21471 E | 18.0 kt | Đến cảng Manila (Philippines) |

- **Khoảng cách:** 447 nm
- **Tốc độ trung bình:** 18.75 kt
- **Số điểm dữ liệu:** 107

Như vậy tau đã hoàn thành một hành trình từ một cảng (Jakarta) đến một cảng khác (Manila) trong ngày 11/09/2026.
**Kiem chung:** PASS (ky vong 1 trong ['447', '448'])

## Luot 2
**Cau hoi:** Trong 3 ngay du lieu, tau nay co lan nao mat tin hieu AIS khong? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps
*(ground truth: gap 2026-09-12 00:14:41 -> 09:43:42)*
**Tra loi:** Có, trong 3 ngày dữ liệu có **mất tín hiệu AIS** duy nhất:

| Ngày | Đoạn mất | Thời gian mất | Đoạn nở | Vị trí bắt đầu (lat/lon) | Vị trí kết thúc (lat/lon) |
|------|----------|---------------|----------|--------------------------|----------------------------|
| 12/09/2026 | 00:14:41 → 09:43:42 UTC | 9 h 28 min |  | 13.0768 N, 111.2685 E (gần cảng Manila) | 15.5762 N, 112.7135 E (gần cảng phía Bắc Philippines) |

- **Độ dài**: 34 141 giây (~9.5 h).
- **Khoảng cách ước tính**: 172 nm, tốc độ ước tính 18 kt.

Vì điểm bắt đầu và kết thúc đều nằm gần các cảng, ta có thể nói **tàu mất tín hiệu tại một cảng (Manila) và xuất hiện lại tại một cảng khác** trong khoảng thời gian này.
**Kiem chung:** PASS (ky vong 1 trong ['12/09', '12-09', '2026-09-12'])

## Luot 3
**Cau hoi:** Ngay 12/09 no di duoc quang duong dai hon hay ngan hon ngay 11/09?
**Tool da goi:** get_journey, get_journeycommentary, get_journey
*(ground truth: day11=447.9nm > day12=213.6nm -> ngan hon)*
**Tra loi:** Ngày 12 / 09, tàu đã đi khoảng **213 nm** (12 điểm dữ liệu) trong khi ngày 11 / 09 tàu đã đi **447 nm** (107 điểm). Vì vậy, quãng đường đi trong ngày 11 / 09 dài hơn đáng kể so với ngày 12 / 09.
**Kiem chung:** FAIL (ky vong 1 trong ['ngắn hơn', 'ngan hon', 'ít hơn', 'it hon'])
