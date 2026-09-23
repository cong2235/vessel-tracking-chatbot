# Kich ban 2 - Duong di va dark gap

## Luot 1
**Cau hoi:** Tau co MMSI 563240200 da di tu dau den dau trong ngay 11/09/2026 (UTC)?
**Tool da goi:** search_vessel, get_journey
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `search_vessel({"query":"563240200"})`
   → `[{"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "mmsi": 563240200, "imo": "9950973", "shipname": "EVER VIVA", "flag": "Singapore (Republic of)", "ship_type_summary": "Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category OS"}]`
2. `get_journey({"vessel_id":"01926a45-3730-7381-9acb-074f84e2e999","start_ts":"2026-09-11T00:00:00Z","end_ts":"2026-09-11T23:59:59Z"})`
   → `{"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "num_points": 107, "distance_nm": 447.93885610550836, "avg_speed_knots": 18.75027478087776, "start_point": {"event_ts": "2026-09-11 00:00:00+00:00", "lat": 6.80919, "lon": 106.98844, "speed_knots": 17.899999618530273}, "end_point": {"event_ts": "2026-09-11 23:53:23+00:00", "lat": 12.9847, "lon": 111.21471, "speed_knots": 18.0}}`

</details>
*(ground truth: distance_nm=447.9 (Ngay 2 da xac minh))*
**Tra loi:** Trong ngày 11/09/2026, tàu có MMSI 563240200 (tên tàu: EVER VIVA) đã khởi hành từ tọa độ 6.80919, 106.98844 vào lúc 00:00 UTC và kết thúc hành trình tại tọa độ 12.9847, 111.21471 vào lúc 23:53 UTC. Tàu đã di chuyển tổng quãng đường khoảng 447.94 hải lý với tốc độ trung bình khoảng 18.75 knot.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['447', '448'])

## Luot 2
**Cau hoi:** Trong 3 ngay du lieu, tau nay co lan nao mat tin hieu AIS khong? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_dark_gaps({"vessel_id":"01926a45-3730-7381-9acb-074f84e2e999","order_by":"duration_desc"})`
   → `{"gaps": [{"gap_id": "01a09500-54b0-7d21-888c-3c8c3d4619a5", "vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "shipname": "EVER VIVA", "gap_start_ts": "2026-09-12 00:14:41+00:00", "gap_end_ts": "2026-09-12 09:43:42+00:00", "gap_duration_seconds": 34141, "distance_nm": 172.0011348741567, "implied_speed_knots": 18.136671027414664, "start_lat": 13.07684326171875, "start_lon": 111.26851654052734, "end_lat": 15.576238632202148, "end_lon": 112.71353149414062}]}`

</details>
*(ground truth: gap 2026-09-12 00:14:41 -> 09:43:42)*
**Tra loi:** Trong 3 ngày dữ liệu gần đây, tàu EVER VIVA đã mất tín hiệu AIS một lần. Cụ thể, tín hiệu bị mất vào lúc 00:14:41 UTC ngày 12/09/2026 tại tọa độ 13.07684, 111.26852 và tín hiệu tái xuất hiện lại vào lúc 09:43:42 UTC cùng ngày tại tọa độ 15.57624, 112.71353. Thời gian mất tín hiệu là khoảng 9 giờ 30 phút.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['12/09', '12-09', '2026-09-12'])

## Luot 3
**Cau hoi:** Ngay 12/09 no di duoc quang duong dai hon hay ngan hon ngay 11/09?
**Tool da goi:** get_journey, get_journey
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_journey({"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "start_ts": "2026-09-11T00:00:00Z", "end_ts": "2026-09-11T23:59:59Z"})`
   → `{"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "num_points": 107, "distance_nm": 447.93885610550836, "avg_speed_knots": 18.75027478087776, "start_point": {"event_ts": "2026-09-11 00:00:00+00:00", "lat": 6.80919, "lon": 106.98844, "speed_knots": 17.899999618530273}, "end_point": {"event_ts": "2026-09-11 23:53:23+00:00", "lat": 12.9847, "lon": 111.21471, "speed_knots": 18.0}}`
2. `get_journey({"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "start_ts": "2026-09-12T00:00:00Z", "end_ts": "2026-09-12T23:59:59Z"})`
   → `{"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "num_points": 12, "distance_nm": 213.64614014215869, "avg_speed_knots": 18.11285364933639, "start_point": {"event_ts": "2026-09-12 00:01:11+00:00", "lat": 13.01846, "lon": 111.2347, "speed_knots": 17.899999618530273}, "end_point": {"event_ts": "2026-09-12 11:48:54+00:00", "lat": 16.16645, "lon": 112.94992, "speed_knots": 17.799999237060547}}`

</details>
*(ground truth: day11=447.9nm > day12=213.6nm -> ngan hon (hoac tuong duong: ngay 11 dai hon))*
**Tra loi:** Vào ngày 11/09/2026, tàu EVER VIVA đã di chuyển quãng đường khoảng 447.94 hải lý. Trong khi đó, vào ngày 12/09/2026, tàu chỉ di chuyển được khoảng 213.65 hải lý. Do đó, ngày 12/09 tàu di được quãng đường ngắn hơn so với ngày 11/09.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['ngắn hơn', 'ngan hon', 'ít hơn', 'it hon', 'dài hơn', 'dai hon'])
