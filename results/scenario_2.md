# Kich ban 2 - Duong di va dark gap

## Luot 1
**Cau hoi:** Tau co MMSI 563240200 da di tu dau den dau trong ngay 11/09/2026 (UTC)?
**Tool da goi:** search_vessel, get_journey
*(ground truth: distance_nm=447.9 (Ngay 2 da xac minh))*
**Tra loi:** Vessel “EVER VIVA” (MMSI 563240200) đã di chuyển trong ngày 11/09/2026, với khoảng cách 447.94 đặm thủy và điểm cuối tại 23:53:23 UTC.
**Kiem chung:** PASS (ky vong 1 trong ['447', '448'])

## Luot 2
**Cau hoi:** Trong 3 ngay du lieu, tau nay co lan nao mat tin hieu AIS khong? Mat o dau va xuat hien lai o dau?
**Tool da goi:** get_dark_gaps
*(ground truth: gap 2026-09-12 00:14:41 -> 09:43:42)*
**Tra loi:** ```json
{
  "hasGap": true,
  "gapCount": 1,
  "gapDetails": [
    {
      "date": "2026-09-12",
      "start": "2026-09-12T00:14:41Z",
      "end": "2026-09-12T09:43:42Z",
      "duration_hours": 9.49,
      "reappeared_at_start": false
    }
  ],
  "gap_at_start_of_period": false
}
```
**Kiem chung:** PASS (ky vong 1 trong ['12/09', '12-09', '2026-09-12'])

## Luot 3
**Cau hoi:** Ngay 12/09 no di duoc quang duong dai hon hay ngan hon ngay 11/09?
**Tool da goi:** get_journey, get_journey
*(ground truth: day11=447.9nm > day12=213.6nm -> ngan hon)*
**Tra loi:** Ngày 12/09 “EVER VIVA” di chuyển khoảng **213.6 nm** trong khi ngày 11/09 di chuyển khoảng **447.9 nm**. Vì vậy ngày 11/09 có quãng đường dài hơn ngày 12/09.
**Kiem chung:** FAIL (ky vong 1 trong ['ngắn hơn', 'ngan hon', 'ít hơn', 'it hon'])
