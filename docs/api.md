# API Reference

Base URL mặc định: `http://localhost:8000` (cấu hình qua `APP_HOST`/`APP_PORT`
trong `.env`). Tài liệu OpenAPI tự sinh (Swagger UI) có sẵn tại `/docs` khi
server đang chạy.

## GET /health

Kiểm tra tình trạng server và kết nối cơ sở dữ liệu.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "database": "ok"}
```

## POST /conversations

Tạo một hội thoại mới.

```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" -d '{"title": "Theo doi tau X"}'
```

```json
{"id": "uuid", "title": "Theo doi tau X", "created_at": "...", "updated_at": "..."}
```

Trường `title` không bắt buộc.

## GET /conversations?limit&offset

Liệt kê hội thoại, sắp xếp mới nhất trước. `limit` mặc định 50 (tối đa 200),
`offset` mặc định 0.

```bash
curl "http://localhost:8000/conversations?limit=10&offset=0"
```

## GET /conversations/{id}/messages

Toàn bộ tin nhắn của một hội thoại, lưu trữ bền vững (còn nguyên sau khi
khởi động lại server). Trả về 404 nếu hội thoại không tồn tại.

```bash
curl http://localhost:8000/conversations/<id>/messages
```

## DELETE /conversations/{id}

Xoá hội thoại, cascade xoá cả tin nhắn và các đoạn bộ nhớ liên quan. Trả về
404 nếu hội thoại không tồn tại.

```bash
curl -X DELETE http://localhost:8000/conversations/<id>
```

## POST /conversations/{id}/chat — streaming (SSE)

Endpoint chính của hệ thống. Trường `message` bắt buộc, độ dài 1–4000 ký tự.

```bash
curl -N -X POST http://localhost:8000/conversations/<id>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho toi thong tin ve tau KOTA GAYA"}'
```

Response có `Content-Type: text/event-stream`, mỗi sự kiện theo định dạng:

```
event: <loai>
data: <json>

```

### Các loại sự kiện

| Sự kiện | `data` | Ý nghĩa |
|---|---|---|
| `token` | chuỗi (mảnh văn bản) | Một phần câu trả lời của model, phát dần theo luồng |
| `tool_call` | `{"name": str, "arguments": {...}}` | Model quyết định gọi một tool |
| `data` | `{"type": "geojson", "tool": str, "geojson": {...}, "summary": {...}}` | Dữ liệu bản đồ (GeoJSON Feature/FeatureCollection) tách khỏi ngữ cảnh gửi cho LLM. `summary` là kết quả của tool sau khi loại bỏ trường `geojson` (ví dụ `distance_nm`, `avg_speed_knots`, `is_stale`, `is_interpolated`), phục vụ hiển thị số liệu trên giao diện bản đồ |
| `done` | `{"answer": str}` | Kết thúc lượt trả lời; `answer` là toàn văn câu trả lời cuối cùng, ghép từ các sự kiện `token` |
| `error` | `{"message": str}` | Lỗi từ LLM, lỗi tool không khôi phục được, hoặc vượt số lần lặp tool tối đa. Kết nối được đóng an toàn, không bị treo |

### Ví dụ một luồng sự kiện

```
event: token
data: "Tau"

event: token
data: " EVER"

event: tool_call
data: {"name": "get_multi_journey_geojson", "arguments": {"vessel_ids": [...], "start_ts": "...", "end_ts": "..."}}

event: data
data: {"type": "geojson", "tool": "get_multi_journey_geojson", "geojson": {"type": "FeatureCollection", "features": [...]}, "summary": {"num_vessels": 23, "total_points": 3018, "bbox": [...], "has_more": false}}

event: done
data: {"answer": "**Hành trình của toàn bộ tàu thuộc Evergreen Marine Corp...**"}
```

## Mã lỗi HTTP

| Mã | Trường hợp |
|---|---|
| 404 | `conversation_id` không tồn tại |
| 422 | Nội dung yêu cầu không hợp lệ (ví dụ `message` rỗng hoặc vượt quá 4000 ký tự) |
| 200 (kèm `event: error` trong luồng) | Lỗi phát sinh sau khi kết nối SSE đã mở — không thể trả mã trạng thái HTTP khác 200 giữa chừng |
