# Kich ban 5 - Nhieu hanh trinh tren ban do (N3)

> **GHI CHU SAU REVIEW (da chay lai qua LLM that, gpt-4o-mini)**: Model
> tung goi `list_vessels_by_type` roi TU BIA bang so lieu tong hop
> ("~3.200 tau, ~5.200.000 nm" - trong khi ca dataset chi co 1.000 tau) o
> lan chay truoc doi model — da sua bang `compare_journeys
> (ship_type_substring=...)` tinh SO THAT tren toan bo tau khop truc tiep
> trong SQL. Luot 2 (so sanh tau xa nhat) nay PASS dung, khop 100% ground
> truth (EVER GLOBE, 1074.66 hai ly). Luot 3 (tau cargo) van chua dung tool
> ky vong (`compare_journeys`) - model chon `list_vessels_by_type`, nhung
> QUAN TRONG: khong con bia so lieu - tra loi trung thuc "628 tau, chi liet
> ke 500 tau do gioi han du lieu" (dung that). Day la but toan chua toi uu
> (thieu so lieu tong hop dung ly), KHONG con la loi bia du lieu nghiem
> trong nhu truoc - ghi nhan trung thuc day la gioi han con lai cua
> gpt-4o-mini o cau hoi nay, khong nhat quan 100% giua cac lan chay (xem
> `docs/research.md` muc 1.4).

## Luot 1
**Cau hoi:** Hien hanh trinh cua tat ca tau do Evergreen Marine Corp khai thac tu ngay 10/09 den het 12/09/2026.
**Tool da goi:** get_company_vessels, get_multi_journey_geojson, get_multi_journey_geojson
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `get_company_vessels({"company_query":"Evergreen Marine Corp"})`
   → `{"matched_companies": [{"company_name": "EVERGREEN MARINE CORP", "match_score": 1.0}, {"company_name": "EVERGREEN MARINE UK LTD", "match_score": 0.5862069}, {"company_name": "EVERGREEN MARINE HONG KONG", "match_score": 0.56666666}, {"company_name": "EVERGREEN MARINE ASIA PTE LTD", "match_score": 0.4857143}, {"company_name": "CHERNAVA MARINE CORP", "match_score": 0.4}, {"company_name": "FPMC 33 MARINE CORP", "match_score": 0.4}], "vessels": [{"vessel_id": "01822507-fa00-736e-b575-8717b43f6f11", "mmsi": 563166100, "shipname": "EVER ATOP", "ship_type_summary": "Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category OS", "roles": ["beneficial_owner", "commercial_manager", "ism_manager", "operator", "registered_owner", "technical_manager"], "matched_company_names": ["E...(rut gon)`
2. `get_multi_journey_geojson({"vessel_ids": ["01822507-fa00-736e-b575-8717b43f6f11", "01616472-7088-77ae-bd73-19848319f969", "016aaf7e-f818-742a-9a62-508a4cad934b", "015dab79-2e80-7f02-901b-e754787339b8", "0164161b-43f8-7e25-af1b-a750c429f7ac", "0164a664-a8a0-7585-b005-d50d5bb1557c", "016684dd-0040-7554-9d8b-620e1ab51fec", "0174f99d-caf0-787f-bd05-20458ecaccb9", "0180874e-a198-7e2a-b1b8-a3684b382ff9", "01668b3c-f198-78d3-88b3-0ddc3e5c2323", "016b4973-9118-70c5-a5ce-3696e0654b65", "014e46f0-c8b0-7a7b-9c7b-ad07c39caa5d", "014e46f2-4b68-72d9-85f4-7e4c094d0ed7", "014e481f-de88-7177-8203-1c3b98cdecfd", "014e4820-1920-7043-9e64-380d7d80b1f5", "0189c395-25d8-7c4c-916f-c69a2680547e", "01921655-54c0-7b5d-8089-8782478bbbdd", "0198313e-9610-7aff-8f63-a6621de0bf9b", "01925b92-a470-7047-a246-7308666a7a51", "017e6a57-fb90-7688-82db-8feefc9ac14f", "014e46eb-9c78-7871-b59d-4bf0982d4780", "019360dc-42a0-774c-9560-d48fbb143b13", "01926a45-3730-7381-9acb-074f84e2e999", "0194f390-7048-72db-b83a-e07547c3baad", "01993772-2eb0-7deb-a945-3f0525d2577c", "01932ea0-c748-7c86-80a5-a89d58efa090", "01906d5c-7048-7b18-909d-f686df6a7e01", "0195ea7e-3ac0-70b7-8a42-d5b2cacf4683", "019279d4-9178-7e44-bf55-e536c1c60c25"], "start_ts": "2026-09-10T00:00:00Z", "end_ts": "2026-09-12T23:59:59Z"})`
   → `{"num_vessels": 29, "total_points": 3956, "bbox": [103.62611, 6.00073, 117.99647, 22.99981], "vessel_names": ["EVER SHINE", "EVER LEADING", "EVER LIBRA", "EVER LIVEN", "EVER LUNAR", "EVER BLISS", "EVER BASIS", "EVER BOOMY", "EVER BRAVE", "EVER BREED", "EVER GIFTED", "EVER BLESS", "EVER GLOBE", "EVER CLEAR", "EVER OATH", "EVER COPE", "EVER ATOP", "EVER MACH", "EVER WIN", "EVER MEMO", "EVER MILD", "EVER VIVA", "EVER WIZ", "EVER WILL", "EVER VERT", "EVER VIVE", "EVER WISH", "EVER META", "EVER WARM"], "page": 1, "page_size": 50, "total_vessels_requested": 29, "has_more": false}`
3. `get_multi_journey_geojson({"vessel_ids": ["016be433-6570-725e-a8a3-27d39ab7a583", "014e46fb-30c0-7e40-9e20-0a9b995cd35b", "01647e42-c758-78a7-9fd3-b4a123a13bdc", "014e49aa-85c8-7f2e-b6b6-63edac111124"], "start_ts": "2026-09-10T00:00:00Z", "end_ts": "2026-09-12T23:59:59Z"})`
   → `{"num_vessels": 4, "total_points": 699, "bbox": [107.30355, 6.05237, 117.96751, 22.35765], "vessel_names": ["MSC UNITE VI", "UNI PERFECT", "NAVIOS BAHAMAS", "FPMC 33"], "page": 1, "page_size": 50, "total_vessels_requested": 4, "has_more": false}`

</details>
*(N3 muc day du: LLM phai tu goi get_company_vessels roi get_multi_journey_geojson; toa do chi tiet di qua su kien `data` (khong qua context LLM) - da verify thu cong co su kien data ~34KB GeoJSON FeatureCollection khi test truoc do.)*
**Tra loi:** Từ ngày 10/09 đến hết ngày 12/09/2026, có tổng cộng 29 tàu do công ty Evergreen Marine Corp khai thác với 3956 điểm theo dõi. Dưới đây là danh sách tên tàu:

1. EVER SHINE
2. EVER LEADING
3. EVER LIBRA
4. EVER LIVEN
5. EVER LUNAR
6. EVER BLISS
7. EVER BASIS
8. EVER BOOMY
9. EVER BRAVE
10. EVER BREED
11. EVER GIFTED
12. EVER BLESS
13. EVER GLOBE
14. EVER CLEAR
15. EVER OATH
16. EVER COPE
17. EVER ATOP
18. EVER MACH
19. EVER WIN
20. EVER MEMO
21. EVER MILD
22. EVER VIVA
23. EVER WIZ
24. EVER WILL
25. EVER VERT
26. EVER VIVE
27. EVER WISH
28. EVER META
29. EVER WARM

Ngoài ra, còn có 4 tàu khác được khai thác từ các công ty khác trong cùng thời gian:

1. MSC UNITE VI
2. UNI PERFECT
3. NAVIOS BAHAMAS
4. FPMC 33

Nếu bạn cần thêm thông tin chi tiết về một tàu cụ thể, hãy cho tôi biết!
**Kiem chung:** PASS (ky vong noi dung 1 trong ['EVER'])

## Luot 2
**Cau hoi:** Trong so do, tau nao di quang duong dai nhat?
**Tool da goi:** compare_journeys
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `compare_journeys({"ship_type_substring":"","start_ts":"2026-09-10T00:00:00Z","end_ts":"2026-09-12T23:59:59Z","vessel_ids":["01822507-fa00-736e-b575-8717b43f6f11","01616472-7088-77ae-bd73-19848319f969","016aaf7e-f818-742a-9a62-508a4cad934b","015dab79-2e80-7f02-901b-e754787339b8","0164161b-43f8-7e25-af1b-a750c429f7ac","0164a664-a8a0-7585-b005-d50d5bb1557c","016684dd-0040-7554-9d8b-620e1ab51fec","0174f99d-caf0-787f-bd05-20458ecaccb9","0180874e-a198-7e2a-b1b8-a3684b382ff9","01668b3c-f198-78d3-88b3-0ddc3e5c2323","016b4973-9118-70c5-a5ce-3696e0654b65","014e46f0-c8b0-7a7b-9c7b-ad07c39caa5d","014e46f2-4b68-72d9-85f4-7e4c094d0ed7","014e481f-de88-7177-8203-1c3b98cdecfd","014e4820-1920-7043-9e64-380d7d80b1f5","0189c395-25d8-7c4c-916f-c69a2680547e","01921655-54c0-7b5d-8089-8782478bbbdd","0198313e-9610-7aff-8f63-a6621de0bf9b","01925b92-a470-7047-a246-7308666a7a51","017e6a57-fb90-7688-82db-8feefc9ac14f","014e46eb-9c78-7871-b59d-4bf0982d4780","019360dc-42a0-774c-9560-d48fbb143b13","01926a45-3730-7381-9acb-074f84e2e999","0194f390-7048-72db-b83a-e07547c3baad","01993772-2eb0-7deb-a945-3f0525d2577c","01932ea0-c748-7c86-80a5-a89d58efa090","01906d5c-7048-7b18-909d-f686df6a7e01","0195ea7e-3ac0-70b7-8a42-d5b2cacf4683","019279d4-9178-7e44-bf55-e536c1c60c25"]})`
   → `{"num_vessels": 29, "vessels": [{"vessel_id": "016b4973-9118-70c5-a5ce-3696e0654b65", "shipname": "EVER GLOBE", "num_points": 220, "distance_nm": 1074.662320973949, "avg_speed_knots": 19.00422132141086}, {"vessel_id": "016684dd-0040-7554-9d8b-620e1ab51fec", "shipname": "EVER BREED", "num_points": 197, "distance_nm": 1038.7081660078136, "avg_speed_knots": 16.168970919448643}, {"vessel_id": "0195ea7e-3ac0-70b7-8a42-d5b2cacf4683", "shipname": "EVER WISH", "num_points": 135, "distance_nm": 1007.8283671157463, "avg_speed_knots": 17.110838151370906}, {"vessel_id": "014e4820-1920-7043-9e64-380d7d80b1f5", "shipname": "EVER LUNAR", "num_points": 270, "distance_nm": 850.7353135057634, "avg_speed_knots": 11.898719579090141}, {"vessel_id": "01926a45-3730-7381-9acb-074f84e2e999", "shipname": "EVER VIVA...(rut gon)`

</details>
*(Ket qua phu thuoc tap tau da xac dinh o luot truoc (co the khac nhau tuy LLM chon loc theo role nao) - ghi nhan de doi chieu thu cong, khong ep 1 dap an cung ve NOI DUNG. Nhung CACH lam kiem chung duoc: phai dung compare_journeys (tinh/xep hang san trong SQL), khong tu goi get_journey tung tau roi so sanh bang tay. Ground truth (toan bo 33 tau bat ke role): EVER GLOBE, 1074.7 nm.)*
**Tra loi:** Tàu đi quãng đường dài nhất trong thời gian từ ngày 10/09 đến hết ngày 12/09/2026 là **EVER GLOBE**, với quãng đường di chuyển là **1074.66 hải lý** và tốc độ trung bình là **19.00 knots**. 

Nếu bạn cần thêm thông tin chi tiết khác, hãy cho tôi biết!
**Kiem chung:** PASS (ky vong da goi tool 1 trong ['compare_journeys'])

## Luot 3
**Cau hoi:** Con toan bo tau cho hang (cargo) trong ngay 11/09 thi sao?
**Tool da goi:** list_vessels_by_type
<details><summary>Chi tiet tool call (tham so + ket qua rut gon)</summary>

1. `list_vessels_by_type({"ship_type_substring":"Cargo"})`
   → `{"vessels": [{"vessel_id": "01a06daa-2f9e-7bd2-83ab-43fe2b6493da", "mmsi": 413463105, "shipname": "017", "ship_type_summary": "Cargo ships, carrying DG and/or MHB, HS, or MP, IMO hazard or pollutant category X"}, {"vessel_id": "018b0e0f-d6e8-7904-a3e9-47bd8e7b7883", "mmsi": 413068558, "shipname": "11", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "017c1419-1e78-713c-a068-b1152c89eb29", "mmsi": 538009593, "shipname": "ACE ETERNITY", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "01836f7c-7538-78bb-a4f8-b734d170b26f", "mmsi": 352005688, "shipname": "ACE GOLD", "ship_type_summary": "Cargo ships, all ships of this type"}, {"vessel_id": "0150e9d9-0b58-7342-a1cc-77d29348175b", "mmsi": 636018913, "shipname": "ACRA", "ship_type_summary": "...(rut gon)`

</details>
*(Ground truth: 628 tau co ship_type_summary chua 'Cargo' - vuot xa gioi han hien thi chi tiet (50 tau/lan). Phat hien that (truoc khi them compare_journeys(ship_type_substring=...)): model goi list_vessels_by_type + vai get_position_at_time mau roi TU BIA ca bang so lieu tong hop (~3200 tau, ~5.200.000 nm - trong khi CA DATASET CHI CO 1000 TAU) - vi pham R4 nghiem trong nhung khong bi phat hien qua kiem tra 'khong crash'. Kiem chung dung: PHAI goi compare_journeys(ship_type_substring='Cargo', ...) - tool nay tinh SO THAT tren TOAN BO tau khop, khong can LLM tu uoc luong.)*
**Tra loi:** Trong ngày 11/09/2026, có tổng cộng **628 tàu** loại hàng (cargo) trong hệ thống. Tuy nhiên, chỉ có **500 tàu** được liệt kê dưới đây, vì dữ liệu bị giới hạn. Nếu bạn cần thêm thông tin hoặc muốn biết thông tin chi tiết về một trong các tàu này, hãy cho tôi biết!

Dưới đây là danh sách một số tàu loại hàng:

1. 017
2. 11
3. ACE ETERNITY
4. ACE GOLD
5. ACRA
6. ADVANTAGE
7. AEGEAN EXPRESS
8. AL MASHRAB
9. AL NASRIYAH
10. ALPHA ETHOS
11. AMOUREUX
12. ANBIEN BAY
13. ANBIEN SKY
14. AN HUA BO 19
15. ANJI LUCK
16. APL CHARLESTON
17. APL RAFFLES
18. APL SALALAH
19. A.P. MOLLER
20. AQUAGRACE
...
(Đây là một phần của danh sách, còn rất nhiều tàu khác)

Nếu bạn muốn tìm hiểu về một tàu cụ thể hoặc cần thêm thông tin, vui lòng cho tôi biết!
**Kiem chung:** FAIL (ky vong da goi tool 1 trong ['compare_journeys'])
