# Kich ban 4 - Dark gap va tra loi khi thieu du lieu

## Luot 1
**Cau hoi:** Tau nao mat tin hieu AIS lau nhat trong du lieu? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps
*(ground truth: gap_duration=229671s, dai nhat toan bo dark_gaps)*
**Tra loi:** Tau “WORLD SPIRIT” là tau có khoảng thời gian mất tín hiệu AIS dài nhất trong dữ liệu.  
- **Bắt đầu mất tín hiệu:** 2026‑09‑10T00:13:09 Z  
- **Tái xuất hiện:** 2026‑09‑12T16:01:00 Z (độ dài khoảng 229 671 giây, tức 63.8 h).
**Kiem chung:** FAIL (ky vong 1 trong ['WORLD SPIRIT'])

## Luot 2
**Cau hoi:** Ai la chu so huu dang ky cua tau do?
**Tool da goi:** get_vessel_info
**Tra loi:** Chủ sở hữu đăng ký của tàu “WORLD SPIRIT” là **MARIGOLD TRANSPORT INC** (đăng ký tại Liberia).
**Kiem chung:** PASS (ky vong 1 trong ['MARIGOLD TRANSPORT'])

## Luot 3
**Cau hoi:** Truoc khi mat tin hieu, tau dang chay voi toc do bao nhieu?
**Tool da goi:** get_position_at_time
**Tra loi:** Tốc độ của tàu “WORLD SPIRIT” trước khi mất tín hiệu là **11,6 hải lý/giờ**.
**Kiem chung:** PASS (ky vong 1 trong ['11.6', '11,6'])
