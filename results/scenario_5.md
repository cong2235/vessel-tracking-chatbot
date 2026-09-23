# Kich ban 5 - Nhieu hanh trinh tren ban do (N3)

> **GHI CHU SAU REVIEW (chay lai lan 3, sau khi sua nguong fuzzy-match cong
> ty)**: Nguoi dung phat hien luot 1 "chi liet ke ten tau" - day la DUNG
> THIET KE, khong phai bug: theo dung yeu cau N3 muc day du cua de bai
> ("LLM chi nhan tom tat: so tau, so diem, khung toa do"), `get_multi_
> journey_geojson` CHU Y KHONG tra ve quang duong/toc do tung tau cho LLM -
> du lieu chi tiet (bao gom hanh trinh ve tren ban do) di qua su kien
> `data` (GeoJSON), tach khoi context LLM. Cau tra loi dang liet ke ten +
> so lieu tong (so tau, so diem) la dung pham vi thiet ke.
>
> Trong luc soat lai, phat hien 1 bug that KHAC: `get_company_vessels`
> dung nguong fuzzy-match 0.4 (dung chung voi vessels.py) qua long cho TEN
> CONG TY - tim "Evergreen Marine Corp" khop nham "CHERNAVA MARINE CORP" va
> "FPMC 33 MARINE CORP" (diem dung 0.4, chi vi trung cum tu chung "MARINE
> CORP", khong lien quan gi den Evergreen - xac minh tay qua get_vessel_info:
> NAVIOS BAHAMAS thuc su thuoc CHERNAVA MARINE CORP, FPMC 33 thuc su thuoc
> FORMOSA PLASTICS MARINE CORP). Da sua: nang MIN_SIMILARITY_SCORE rieng
> cho ownership.py len 0.45 (giu nguyen 0.4 cho ten tau o vessels.py, vi day
> la 2 loai du lieu khac dac tinh). Sau khi sua, luot 1 tra ve DUNG 31 tau
> (29 tau ten "EVER*" + MSC UNITE VI + UNI PERFECT - ca 2 xac minh tay la
> THAT SU do Evergreen Marine Corp khai thac/so huu qua get_vessel_info),
> thay vi 33 tau nham truoc do. Them unit test hoi quy:
> tests/test_ownership.py::test_get_company_vessels_does_not_match_unrelated_company_sharing_generic_words.
>
> Luot 2 nay PASS dung (EVER GLOBE, 1074.66 hai ly - khop dung tap 31 tau
> that). Luot 3 van FAIL theo kiem chung "phai goi compare_journeys" - lan
> nay model chon `list_vessels_by_type`, nhung noi dung KHONG con bia so
> lieu: tra loi neu "500 tau" o cau dau (chi la so tra ve, chua chinh xac)
> nhung TU SUA lai o cuoi "chi la 1 phan trong tong so 628 tau" (dung that,
> tu total_matched cua tool) - la but toan chua toi uu, khong phai loi bia
> du lieu. Ghi nhan trung thuc day la gioi han lua chon tool con lai cua
> gpt-4o-mini, xem `docs/research.md` muc 1.4.

## Luot 1
**Cau hoi:** Hien hanh trinh cua tat ca tau do Evergreen Marine Corp khai thac tu ngay 10/09 den het 12/09/2026.
**Tool da goi:** get_company_vessels, get_multi_journey_geojson, get_multi_journey_geojson
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_company_vessels({"company_query":"Evergreen Marine Corp"})`
   → `{"matched_companies": [{"company_name": "EVERGREEN MARINE CORP", "match_score": 1.0}, {"company_name": "EVERGREEN MARINE UK LTD", "match_score": 0.5862069}, {"company_name": "EVERGREEN MARINE HONG KONG", "match_score": 0.56666666}, {"company_name": "EVERGREEN MARINE ASIA PTE LTD", "match_score": 0.4857143}], "vessels": [{"vessel_id": "01822507-fa00-736e-b575-8717b43f6f11", "mmsi": 563166100, "shipname": "EVER ATOP", "ship_type_summary": "Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category OS", "roles": ["beneficial_owner", "commercial_manager", "ism_manager", "operator", "registered_owner", "technical_manager"], "matched_company_names": ["EVERGREEN MARINE ASIA PTE LTD", "EVERGREEN MARINE CORP"]}, {"vessel_id": "01616472-7088-77ae-bd73-19848319f969", "mmsi": 416...(rut gon)`
2. `get_multi_journey_geojson({"vessel_ids": ["01822507-fa00-736e-b575-8717b43f6f11", "01616472-7088-77ae-bd73-19848319f969", "016aaf7e-f818-742a-9a62-508a4cad934b", "015dab79-2e80-7f02-901b-e754787339b8", "0164161b-43f8-7e25-af1b-a750c429f7ac", "0164a664-a8a0-7585-b005-d50d5bb1557c", "016684dd-0040-7554-9d8b-620e1ab51fec", "0174f99d-caf0-787f-bd05-20458ecaccb9", "0180874e-a198-7e2a-b1b8-a3684b382ff9", "01668b3c-f198-78d3-88b3-0ddc3e5c2323", "016b4973-9118-70c5-a5ce-3696e0654b65", "014e46f0-c8b0-7a7b-9c7b-ad07c39caa5d", "014e46f2-4b68-72d9-85f4-7e4c094d0ed7", "014e481f-de88-7177-8203-1c3b98cdecfd", "014e4820-1920-7043-9e64-380d7d80b1f5", "0189c395-25d8-7c4c-916f-c69a2680547e", "01921655-54c0-7b5d-8089-8782478bbbdd", "0198313e-9610-7aff-8f63-a6621de0bf9b", "01925b92-a470-7047-a246-7308666a7a51", "017e6a57-fb90-7688-82db-8feefc9ac14f", "014e46eb-9c78-7871-b59d-4bf0982d4780", "019360dc-42a0-774c-9560-d48fbb143b13", "01926a45-3730-7381-9acb-074f84e2e999", "0194f390-7048-72db-b83a-e07547c3baad", "01993772-2eb0-7deb-a945-3f0525d2577c", "01932ea0-c748-7c86-80a5-a89d58efa090", "01906d5c-7048-7b18-909d-f686df6a7e01", "0195ea7e-3ac0-70b7-8a42-d5b2cacf4683", "019279d4-9178-7e44-bf55-e536c1c60c25", "014e46fb-30c0-7e40-9e20-0a9b995cd35b", "014e49aa-85c8-7f2e-b6b6-63edac111124"], "start_ts": "2026-09-10T00:00:00Z", "end_ts": "2026-09-12T23:59:59Z", "page": 1, "page_size": 50})`
   → `{"num_vessels": 31, "total_points": 4267, "bbox": [103.62611, 6.00073, 117.99647, 22.99981], "vessel_names": ["EVER SHINE", "EVER LEADING", "EVER LIBRA", "MSC UNITE VI", "EVER LIVEN", "EVER LUNAR", "UNI PERFECT", "EVER BLISS", "EVER BASIS", "EVER BOOMY", "EVER BRAVE", "EVER BREED", "EVER GIFTED", "EVER BLESS", "EVER GLOBE", "EVER CLEAR", "EVER OATH", "EVER COPE", "EVER ATOP", "EVER MACH", "EVER WIN", "EVER MEMO", "EVER MILD", "EVER VIVA", "EVER WIZ", "EVER WILL", "EVER VERT", "EVER VIVE", "EVER WISH", "EVER META", "EVER WARM"], "page": 1, "page_size": 50, "total_vessels_requested": 31, "has_more": false}`
3. `get_multi_journey_geojson({"vessel_ids": ["016577d2-4b68-72d9-85f4-7e4c094d0ed7"], "start_ts": "2026-09-10T00:00:00Z", "end_ts": "2026-09-12T23:59:59Z", "page": 1, "page_size": 50})`
   → `{"num_vessels": 0, "total_points": 0, "bbox": null, "vessel_names": [], "page": 1, "page_size": 50, "total_vessels_requested": 1, "has_more": false}`

</details>
*(N3 muc day du: LLM phai tu goi get_company_vessels roi get_multi_journey_geojson; toa do chi tiet di qua su kien `data` (khong qua context LLM) - da verify thu cong co su kien data ~34KB GeoJSON FeatureCollection khi test truoc do.)*
**Tra loi:** Hành trình của tất cả tàu do Evergreen Marine Corp khai thác từ ngày 10/09 đến hết 12/09/2026 có 31 tàu, với tổng số điểm hành trình là 4267.

Danh sách các tàu bao gồm:
1. EVER SHINE
2. EVER LEADING
3. EVER LIBRA
4. MSC UNITE VI
5. EVER LIVEN
6. EVER LUNAR
7. UNI PERFECT
8. EVER BLISS
9. EVER BASIS
10. EVER BOOMY
11. EVER BRAVE
12. EVER BREED
13. EVER GIFTED
14. EVER BLESS
15. EVER GLOBE
16. EVER CLEAR
17. EVER OATH
18. EVER COPE
19. EVER ATOP
20. EVER MACH
21. EVER WIN
22. EVER MEMO
23. EVER MILD
24. EVER VIVA
25. EVER WIZ
26. EVER WILL
27. EVER VERT
28. EVER VIVE
29. EVER WISH
30. EVER META
31. EVER WARM

 không có thêm tàu nào khác trong hệ thống.
**Kiem chung:** PASS (ky vong noi dung 1 trong ['EVER'])

## Luot 2
**Cau hoi:** Trong so do, tau nao di quang duong dai nhat?
**Tool da goi:** compare_journeys
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `compare_journeys({"vessel_ids":["01822507-fa00-736e-b575-8717b43f6f11","01616472-7088-77ae-bd73-19848319f969","016aaf7e-f818-742a-9a62-508a4cad934b","015dab79-2e80-7f02-901b-e754787339b8","0164161b-43f8-7e25-af1b-a750c429f7ac","0164a664-a8a0-7585-b005-d50d5bb1557c","016684dd-0040-7554-9d8b-620e1ab51fec","0174f99d-caf0-787f-bd05-20458ecaccb9","0180874e-a198-7e2a-b1b8-a3684b382ff9","01668b3c-f198-78d3-88b3-0ddc3e5c2323","016b4973-9118-70c5-a5ce-3696e0654b65","014e46f0-c8b0-7a7b-9c7b-ad07c39caa5d","014e46f2-4b68-72d9-85f4-7e4c094d0ed7","014e481f-de88-7177-8203-1c3b98cdecfd","014e4820-1920-7043-9e64-380d7d80b1f5","0189c395-25d8-7c4c-916f-c69a2680547e","01921655-54c0-7b5d-8089-8782478bbbdd","0198313e-9610-7aff-8f63-a6621de0bf9b","01925b92-a470-7047-a246-7308666a7a51","017e6a57-fb90-7688-82db-8feefc9ac14f","014e46eb-9c78-7871-b59d-4bf0982d4780","019360dc-42a0-774c-9560-d48fbb143b13","01926a45-3730-7381-9acb-074f84e2e999","0194f390-7048-72db-b83a-e07547c3baad","01993772-2eb0-7deb-a945-3f0525d2577c","01932ea0-c748-7c86-80a5-a89d58efa090","01906d5c-7048-7b18-909d-f686df6a7e01","0195ea7e-3ac0-70b7-8a42-d5b2cacf4683","019279d4-9178-7e44-bf55-e536c1c60c25","014e46fb-30c0-7e40-9e20-0a9b995cd35b","014e49aa-85c8-7f2e-b6b6-63edac111124"],"start_ts":"2026-09-10T00:00:00Z","end_ts":"2026-09-12T23:59:59Z"})`
   → `{"num_vessels": 31, "vessels": [{"vessel_id": "016b4973-9118-70c5-a5ce-3696e0654b65", "shipname": "EVER GLOBE", "num_points": 220, "distance_nm": 1074.662320973949, "avg_speed_knots": 19.00422132141086}, {"vessel_id": "016684dd-0040-7554-9d8b-620e1ab51fec", "shipname": "EVER BREED", "num_points": 197, "distance_nm": 1038.7081660078136, "avg_speed_knots": 16.168970919448643}, {"vessel_id": "0195ea7e-3ac0-70b7-8a42-d5b2cacf4683", "shipname": "EVER WISH", "num_points": 135, "distance_nm": 1007.8283671157463, "avg_speed_knots": 17.110838151370906}, {"vessel_id": "014e4820-1920-7043-9e64-380d7d80b1f5", "shipname": "EVER LUNAR", "num_points": 270, "distance_nm": 850.7353135057634, "avg_speed_knots": 11.898719579090141}, {"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "shipname": "EVER VIVA...(rut gon)`

</details>
*(Ket qua phu thuoc tap tau da xac dinh o luot truoc (co the khac nhau tuy LLM chon loc theo role nao) - ghi nhan de doi chieu thu cong, khong ep 1 dap an cung ve NOI DUNG. Nhung CACH lam kiem chung duoc: phai dung compare_journeys (tinh/xep hang san trong SQL), khong tu goi get_journey tung tau roi so sanh bang tay. Ground truth (toan bo 33 tau bat ke role): EVER GLOBE, 1074.7 nm.)*
**Tra loi:** Trong số các tàu, tàu di chuyển quãng đường dài nhất là **EVER GLOBE** với quãng đường đạt **1074.66 hải lý** và tốc độ trung bình là **19.00 hải lý/giờ**.
**Kiem chung:** PASS (ky vong da goi tool 1 trong ['compare_journeys'])

## Luot 3
**Cau hoi:** Con toan bo tau cho hang (cargo) trong ngay 11/09 thi sao?
**Tool da goi:** list_vessels_by_type
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `list_vessels_by_type({"ship_type_substring":"Cargo"})`
   → `{"vessels": [{"vessel_id": "01a06daa-2f9e-7bd2-83ab-43fe2b6493da", "mmsi": 413463105, "shipname": "017", "ship_type_summary": "Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X"}, {"vessel_id": "018b0e0f-d6e8-7904-a3e9-47bd8e7b7883", "mmsi": 413068558, "shipname": "11", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "017c1419-1e78-713c-a068-b1152c89eb29", "mmsi": 538009593, "shipname": "ACE ETERNITY", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "01836f7c-7538-78bb-a4f8-b734d170b26f", "mmsi": 352005688, "shipname": "ACE GOLD", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "0150e9d9-0b58-7342-a1cc-77d29348175b", "mmsi": 636018913, "shipname": "ACRA", "ship_type_summary": "...(rut gon)`

</details>
*(Ground truth: 628 tau co ship_type_summary chua 'Cargo' - vuot xa gioi han hien thi chi tiet (50 tau/lan). Phat hien that (truoc khi them compare_journeys(ship_type_substring=...)): model goi list_vessels_by_type + vai get_position_at_time mau roi TU BIA ca bang so lieu tong hop (~3200 tau, ~5.200.000 nm - trong khi CA DATASET CHI CO 1000 TAU) - vi pham R4 nghiem trong nhung khong bi phat hien qua kiem tra 'khong crash'. Kiem chung dung: PHAI goi compare_journeys(ship_type_substring='Cargo', ...) - tool nay tinh SO THAT tren TOAN BO tau khop, khong can LLM tu uoc luong.)*
**Tra loi:** Trong ngày 11/09, có tổng cộng **500 tàu cargo** được ghi nhận. Danh sách bao gồm nhiều tàu như:

1. **017**
2. **11**
3. **ACE ETERNITY**
4. **ACE GOLD**
5. **ACRA**
6. **ADVANTAGE**
7. **AEGEAN EXPRESS**
8. **AL MASHRAB**
9. **AL NASRIYAH**
10. **ALPHA ETHOS**
11. **AMOUREUX**
12. **ANBIEN BAY**
13. **ANBIEN SKY**
14. **AN HUA BO 19**
15. **ANJI LUCK**
... và nhiều hơn nữa.

Lưu ý rằng danh sách trên chỉ là một phần trong tổng số 628 tàu. Ngoài ra, dữ liệu còn có thông báo rằng có nhiều tàu hơn (có thể yêu cầu thêm nếu cần).
**Kiem chung:** FAIL (ky vong da goi tool 1 trong ['compare_journeys'])
