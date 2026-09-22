# API Reference

Base URL mặc định: `http://localhost:8000` (xem `APP_HOST`/`APP_PORT` trong
`.env`). OpenAPI tự sinh (Swagger UI) có sẵn tại `/docs` khi chạy server.

## GET /health

Kiểm tra server + kết nối DB.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "database": "ok"}
```

## POST /conversations

Tạo hội thoại mới.

```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" -d '{"title": "Theo doi tau X"}'
```

```json
{"id": "uuid", "title": "Theo doi tau X", "created_at": "...", "updated_at": "..."}
```

`title` không bắt buộc.

## GET /conversations?limit&offset

Liệt kê hội thoại, mới nhất trước. `limit` mặc định 50 (tối đa 200),
`offset` mặc định 0.

```bash
curl "http://localhost:8000/conversations?limit=10&offset=0"
```

## GET /conversations/{id}/messages

Toàn bộ tin nhắn của 1 hội thoại (persist bền vững — restart server vẫn
xem được). 404 nếu không tồn tại.

```bash
curl http://localhost:8000/conversations/<id>/messages
```

## DELETE /conversations/{id}

Xoá hội thoại (cascade xoá cả messages, memory_chunks). 404 nếu không tồn tại.

```bash
curl -X DELETE http://localhost:8000/conversations/<id>
```

## POST /conversations/{id}/chat — streaming (SSE)

Endpoint chính. `message` bắt buộc, 1–4000 ký tự.

```bash
curl -N -X POST http://localhost:8000/conversations/<id>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho toi thong tin ve tau KOTA GAYA"}'
```

Response: `Content-Type: text/event-stream`, mỗi sự kiện dạng:

```
event: <loai>
data: <json>

```

### Các loại sự kiện

| Sự kiện | `data` | Khi nào |
|---|---|---|
| `token` | chuỗi (mảnh text) | Model đang sinh câu trả lời, đến dần |
| `tool_call` | `{"name": str, "arguments": {...}}` | Model quyết định gọi 1 tool |
| `data` | `{"type": "geojson", "tool": str, "geojson": {...}}` | Tool trả về dữ liệu bản đồ (N2/N3) — GeoJSON Feature/FeatureCollection, KHÔNG đi qua context LLM |
| `done` | `{"answer": str}` | Kết thúc lượt, `answer` là toàn văn câu trả lời cuối (đã ghép từ các `token`) |
| `error` | `{"message": str}` | LLM lỗi, tool lỗi không phục hồi được, hoặc vượt số lần lặp tool tối đa — kết nối vẫn đóng gọn gàng, không treo |

### Ví dụ luồng thật (rút gọn, đã chạy verify)

```
event: token
data: "Tau"

event: token
data: " EVER"

event: tool_call
data: {"name": "get_multi_journey_geojson", "arguments": {"vessel_ids": [...], "start_ts": "...", "end_ts": "..."}}

event: data
data: {"type": "geojson", "tool": "get_multi_journey_geojson", "geojson": {"type": "FeatureCollection", "features": [...]}}

event: done
data: {"answer": "**Hành trình của toàn bộ tàu thuộc Evergreen Marine Corp...**"}
```

## Mã lỗi HTTP

| Code | Khi nào |
|---|---|
| 404 | `conversation_id` không tồn tại |
| 422 | Body không hợp lệ (vd. `message` rỗng hoặc > 4000 ký tự) |
| 200 (nhưng SSE có `event: error`) | Lỗi xảy ra SAU khi stream đã mở — không thể trả HTTP status code khác 200 giữa chừng |
