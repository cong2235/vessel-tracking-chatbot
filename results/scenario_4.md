# Kich ban 4 - Dark gap va tra loi khi thieu du lieu

## Luot 1
**Cau hoi:** Tau nao mat tin hieu AIS lau nhat trong du lieu? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps
*(ground truth: gap_duration=229671s, dai nhat toan bo dark_gaps)*
**Tra loi:** Tàu **“WORLD SPIRIT”** là tàu mất tín hiệu AIS dài nhất trong dữ liệu.  
- **Bắt đầu mất tín hiệu:** 2026‑09‑10 00:13:09 UTC  
- **Tái xuất hiện:** 2026‑09‑12 16:01:00 UTC  
- **Thời gian mất tín hiệu:** 229 671 giây (khoảng 63.8 giờ).
**Kiem chung:** PASS (ky vong 1 trong ['WORLD SPIRIT'])

## Luot 2
**Cau hoi:** Ai la chu so huu dang ky cua tau do?
**Tool da goi:** get_vessel_info
**Tra loi:** Chủ sở hữu đăng ký của tàu **WORLD SPIRIT** là **Marigold Transport Inc.** (quốc gia: Liberia).
**Kiem chung:** PASS (ky vong 1 trong ['MARIGOLD TRANSPORT'])

## Luot 3
**Cau hoi:** Truoc khi mat tin hieu, tau dang chay voi toc do bao nhieu?
**Tool da goi:** get_position_at_time
**Tra loi:** Trước khi mất tín hiệu, tàu **WORLD SPIRIT** đang chạy với tốc độ **11,6 knots** (khoảng 21,4 km/h) tại thời điểm 2026‑09‑10 00:03:03 UTC.
**Kiem chung:** PASS (ky vong 1 trong ['11.6', '11,6'])
