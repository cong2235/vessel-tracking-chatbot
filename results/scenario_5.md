# Kich ban 5 - Nhieu hanh trinh tren ban do (N3)

## Luot 1
**Cau hoi:** Hien hanh trinh cua tat ca tau do Evergreen Marine Corp khai thac tu ngay 10/09 den het 12/09/2026.
**Tool da goi:** get_company_vessels, get_multi_journey_geojson
*(N3 muc day du: LLM phai tu goi get_company_vessels roi get_multi_journey_geojson; toa do chi tiet di qua su kien `data` (khong qua context LLM) - da verify thu cong co su kien data ~34KB GeoJSON FeatureCollection khi test truoc do.)*
**Tra loi:** ```json
{
  "num_vessels": 33,
  "total_points": 4655,
  "bbox": [103.62611, 6.00073, 117.99647, 22.99981],
  "vessel_names": [
    "EVER SHINE",
    "EVER LEADING",
    "EVER LIBRA",
    "MSC UNITE VI",
    "EVER LIVEN",
    "EVER LUNAR",
    "UNI PERFECT",
    "EVER BLISS",
    "EVER BASIS",
    "EVER BOOMY",
    "NAVIOS BAHAMAS",
    "EVER BRAVE",
    "EVER BREED",
    "EVER GIFTED",
    "EVER BLESS",
    "EVER GLOBE",
    "FPMC 33",
    "EVER CLEAR",
    "EVER OATH",
    "EVER COPE",
    "EVER ATOP",
    "EVER MACH",
    "EVER WIN",
    "EVER MEMO",
    "EVER MILD",
    "EVER VIVA",
    "EVER WIZ",
    "EVER WILL",
    "EVER VERT",
    "EVER VIVE",
    "EVER WISH",
    "EVER META",
    "EVER WARM"
  ]
}
```
**Kiem chung:** PASS (ky vong 1 trong ['EVER'])

## Luot 2
**Cau hoi:** Trong so do, tau nao di quang duong dai nhat?
*(Ket qua phu thuoc tap tau da xac dinh o luot truoc (co the khac nhau tuy LLM chon loc theo role nao) - ghi nhan de doi chieu thu cong, khong ep 1 dap an cung. Ground truth (toan bo 33 tau bat ke role): EVER GLOBE, 1074.7 nm.)*
**Tra loi:** [LOI: Error code: 500 - {'errors': [{'message': 'AiError: AiError: Internal server error (232497d5-66c7-4764-8556-2cd817872d49)', 'code': 3043}], 'success': False, 'result': {}, 'messages': []}]

## Luot 3
**Cau hoi:** Con toan bo tau cho hang (cargo) trong ngay 11/09 thi sao?
*(Ground truth: 628 tau co ship_type_summary chua 'Cargo' - vuot MAX_VESSELS_PER_REQUEST=50, kiem tra tool co tu gioi han dung khong (khong crash/treo) thay vi ep 1 dap an cu the.)*
**Tra loi:** [LOI: Error code: 500 - {'errors': [{'message': 'AiError: AiError: Internal server error (76bfa47f-6894-4f37-b414-07ee6eb707eb)', 'code': 3043}], 'success': False, 'result': {}, 'messages': []}]
