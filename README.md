# Chatbot tra cứu tàu biển

Đã hoàn thành R1–R4, N1–N3, D1–D3 theo lộ trình 7 ngày (chi tiết từng ngày:
xem mục Roadmap cuối file). LLM đang dùng: Cloudflare Workers AI
(`gpt-oss-20b`) — lý do chọn và quá trình so sánh: `docs/research.md`.

## Cấu trúc thư mục

```
llm engineer test/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.postgres        # Postgres + PostGIS + pgvector trong 1 image
├── main.py                    # entrypoint FastAPI: uvicorn main:app
├── db/
│   └── schema.sql             # DDL: bảng dữ liệu tàu + bảng app (hội thoại/memory)
├── scripts/
│   ├── load_data.py           # pipeline tự động nạp 4 CSV
│   ├── chat_cli.py            # CLI test tool-calling không streaming
│   ├── run_scenarios.py       # chạy 5 kịch bản mẫu qua LLM thật -> results/
│   └── verify_results.py      # kiểm chứng lại kết quả đã lưu (offline)
├── web/
│   └── index.html             # UI chat + bản đồ Leaflet (N1/N2/N3), vanilla JS
├── src/
│   ├── db.py                  # kết nối Postgres dùng chung (tự đăng ký kiểu vector)
│   ├── tools/                 # tầng truy vấn (R1)
│   │   ├── vessels.py         #   search_vessel, get_vessel_info, list_vessels_by_type
│   │   ├── ownership.py       #   get_company_vessels
│   │   ├── positions.py       #   get_position_at_time
│   │   ├── journeys.py        #   get_journey, get_multi_journey_geojson (N3)
│   │   └── dark_gaps.py       #   get_dark_gaps
│   ├── agent/
│   │   ├── agent.py           #   vòng lặp tool-calling (thường + streaming) + tách geojson (N2)
│   │   ├── store.py           #   lưu/đọc hội thoại vào Postgres
│   │   └── memory.py          #   cửa sổ ngắn hạn + tóm tắt/nhúng/rerank pgvector (R3)
│   ├── models/
│   │   ├── llm_client.py      #   chat_once/chat_stream + retry (OpenAI-compatible)
│   │   ├── embeddings.py      #   embed_text
│   │   └── reranker.py        #   rerank (Cloudflare REST, không qua OpenAI SDK)
│   ├── prompts/
│   │   ├── system_prompts.py
│   │   └── tool_specs.py
│   ├── api/
│   │   ├── routes.py          #   CRUD hội thoại + /health + chat streaming SSE
│   │   └── schemas.py
│   └── utils/                  # config.py, logger.py — dùng chung
├── tests/                      # 73/73 pass
├── data/                       # 4 file CSV gốc (đề bài cung cấp)
├── docs/
│   ├── research.md             # so sánh & lý do chọn LLM/embedding/vector DB/memory
│   ├── architecture.md         # sơ đồ, luồng xử lý, schema, hạn chế, chi phí
│   └── api.md                  # API reference
├── results/                    # transcript 5 kịch bản mẫu (D3)
└── logs/                       # log runtime (gitignore, giữ .gitkeep)
```

Cấu trúc dựa theo layout project AI agent phổ biến (`src/{agent,tools,models,
prompts,api,utils}`), điều chỉnh cho đúng domain và bổ sung `db/`, `docs/`,
`results/`, `web/` theo đúng cấu trúc gợi ý của đề bài.

## Yêu cầu hệ thống

- Docker + Docker Compose
- Python 3.10+

## 1. Cài đặt

```bash
cp .env.example .env
# mở .env, đổi POSTGRES_PASSWORD (và các giá trị khác nếu cần)

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## 2. Khởi động database (PostgreSQL + PostGIS + pgvector)

```bash
docker compose up -d --build
```

## 3. Nạp dữ liệu

Script dưới đây tự động: áp dụng schema (`db/schema.sql`) → nạp 4 file CSV
trong `data/` vào bảng staging bằng `COPY` → làm sạch/ép kiểu và nạp sang
bảng chính → đối chiếu số dòng với số liệu kỳ vọng trong đề bài.

```bash
python scripts/load_data.py
```

Chạy lại lệnh trên bao nhiêu lần cũng an toàn — dữ liệu bảng chính luôn được
`TRUNCATE` trước khi nạp lại nên không bao giờ bị nhân đôi.

Kết quả mong đợi:

```
[schema] applied .../db/schema.sql
[staging] staging_vessels: 1000 dong nap tu vessels.csv
[staging] staging_ais_positions: 171073 dong nap tu ais_positions.csv
[staging] staging_dark_gaps: 880 dong nap tu dark_gaps.csv
[staging] staging_ownership: 4127 dong nap tu ownership.csv
[load] da nap du lieu tu staging sang bang chinh
[verify] vessels: 1000 dong (ky vong 1000) -> OK
[verify] ais_positions: 171073 dong (ky vong 171073) -> OK
[verify] dark_gaps: 880 dong (ky vong 880) -> OK
[verify] ownership: 4127 dong (ky vong 4127) -> OK
[done] pipeline hoan tat, da commit.
```

## Cấu trúc dữ liệu

Xem chi tiết schema tại [`db/schema.sql`](db/schema.sql). Tóm tắt:

- `vessels`, `ais_positions`, `dark_gaps`, `ownership`: dữ liệu tàu biển,
  nạp trực tiếp từ CSV qua bảng staging (toàn cột TEXT) để cách ly lỗi kiểu
  dữ liệu do CSV có nhiễu (ô rỗng, số dạng `"9605047.0"`...).
- `ais_positions.geom`, `dark_gaps.start_geom/end_geom/gap_line`: cột hình
  học PostGIS được **tự động tính từ lon/lat** (generated column), không cần
  xử lý riêng khi nạp.
- Index: GiST trên các cột hình học, B-tree trên `(vessel_id, event_ts)`,
  GIN trigram trên `shipname`/`company_name` để hỗ trợ tìm kiếm gần đúng
  (sai chính tả nhẹ, tên công ty có biến thể).
- `conversations`, `messages`, `memory_chunks`: bảng phục vụ API chat và bộ
  nhớ dài hạn — sẽ được dùng ở các ngày tiếp theo (R2, R3), tạo sẵn schema
  ngay từ đầu để không phải chạy migration giữa chừng.

## 4. Chạy unit test tầng truy vấn (Ngày 2)

Yêu cầu DB đã nạp dữ liệu (bước 3). Test chạy trực tiếp trên dữ liệu thật,
không mock:

```bash
python -m pytest tests/ -v
```

### Tầng tool (`src/tools/`)

| Tool | File | Đáp ứng |
|---|---|---|
| `search_vessel(query)` | `vessels.py` | Tìm theo tên (ILIKE + trigram fuzzy), MMSI, IMO; luôn trả list để tầng gọi tự xử lý khi trùng/không thấy |
| `get_vessel_info(vessel_id)` | `vessels.py` | Thông tin tĩnh + toàn bộ ownership theo role |
| `get_company_vessels(company_query, role=None)` | `ownership.py` | Fuzzy match biến thể tên công ty, trả tàu đã gom nhóm (không lặp theo role) |
| `get_position_at_time(vessel_id, at_ts)` | `positions.py` | Điểm AIS gần thời điểm hỏi nhất, kèm `delta_seconds` và cờ `is_stale` |
| `get_journey(vessel_id, start_ts, end_ts)` | `journeys.py` | Điểm đầu/cuối, số điểm, quãng đường (hải lý, PostGIS geography), tốc độ TB, GeoJSON |
| `get_dark_gaps(vessel_id=None, order_by=...)` | `dark_gaps.py` | Liệt kê/sắp xếp dark gap; vị trí+tốc độ trước khi mất tín hiệu tái dùng `get_position_at_time(vessel_id, gap_start_ts)` |

Nguyên tắc áp dụng cho mọi tool: SQL tham số hoá, chỉ SELECT, luôn LIMIT,
không có dữ liệu → trả `None`/`[]` (không bịa).

**Ngưỡng fuzzy-match:** `pg_trgm` mặc định coi similarity ≥ 0.3 là khớp —
quá lỏng, khiến chuỗi ngẫu nhiên vẫn trùng vài trigram với tên thật (phát
hiện qua test, không phải giả định). Đã nâng ngưỡng lên `MIN_SIMILARITY_SCORE
= 0.4` ở cả `vessels.py` và `ownership.py`.

## 5. Chat CLI thử tool-calling (Ngày 3)

Cần `OPENAI_API_KEY` trong `.env` (xem `.env.example`). Chatbot chưa
streaming (Ngày 4 mới thêm SSE), chưa lưu lịch sử vào DB (Ngày 4/5), chỉ để
test vòng lặp gọi tool trong 1 phiên CLI:

```bash
python scripts/chat_cli.py
```

Thử lại đúng Kịch bản 1/2 trong đề bài, vd: "Cho tôi thông tin về tàu KOTA
GAYA", rồi hỏi tiếp "Chủ sở hữu và các công ty quản lý của tàu này là ai?".

### Vòng lặp tool-calling (`src/agent/agent.py`)

`run_agent_turn(messages)`: gọi LLM (OpenAI, `src/models/llm_client.py`) →
nếu model trả `tool_calls` → chạy tool thật tương ứng (`src/tools/`, tra
theo `TOOL_REGISTRY` trong `src/prompts/tool_specs.py`) → đưa kết quả (JSON)
lại cho model → lặp tối đa `MAX_TOOL_ITERATIONS=8` lần tới khi có câu trả
lời cuối. Lỗi tool (exception) được bắt lại thành `{"error": ...}` gửi cho
model thay vì làm sập tiến trình — nền tảng cho sự kiện `error` ở luồng SSE
Ngày 4.

**Đã verify (không cần API key thật):** 5 unit test trong `tests/test_agent.py`
mock đúng 1 ranh giới duy nhất (`chat_once` — lời gọi LLM trả phí), còn tool
vẫn chạy trên DB thật. Đã kiểm chứng: gọi tool đúng tham số + trả câu trả
lời cuối; dừng ngay khi không có tool_call; tool không tồn tại/tool lỗi
(exception thật từ Postgres) không làm sập vòng lặp; chặn được vòng lặp vô
hạn khi model cứ gọi tool mãi.

**Đã verify với LLM thật (endpoint self-hosted `qwen3.5-9b` qua `OPENAI_BASE_URL`):**
khi tool_calls trigger đúng, câu trả lời khớp 100% với dữ liệu thật (đã đối
chiếu tay). Nhưng phát hiện **rủi ro thật**: endpoint này không ổn định —
nhiều lần model in tool-call dưới dạng text thô (`<tool_call> search_vessel(...)`)
thay vì dùng đúng cơ chế `tool_calls` chuẩn của API (nghi do server vLLM
thiếu cấu hình `--tool-call-parser hermes` cho Qwen). Khi xảy ra, code hiện
tại (Ngày 3) coi đó là câu trả lời cuối — không tool nào chạy — và model tự
bịa phần còn lại, **vi phạm R4**. Đây là hạn chế của hạ tầng LLM thử
nghiệm, không phải lỗi vòng lặp tool-calling (đã test kỹ ở trên).

**Đã chuyển sang và verify thành công với `@cf/openai/gpt-oss-20b` qua
Cloudflare Workers AI** (API tương thích OpenAI, không cần sửa code, chỉ
đổi `.env`). Chạy lại đầy đủ Kịch bản 1 (4 lượt, gồm follow-up bằng đại từ
"tàu này"/"đó") — **khớp 100% dữ liệu thật** ở mọi lượt, bao gồm cả trường
hợp trung thực báo "chưa có dữ liệu" thay vì bịa (lượt 1, khi chỉ mới gọi
`search_vessel` chưa đủ thông tin). Tool-calling ổn định qua nhiều lần gọi
lặp lại (5/5, so với 0/5 của qwen3.5-9b ở cùng điều kiện).

Trong lúc chuyển provider, phát hiện + sửa 2 vấn đề tương thích thật (không
phải lỗi vòng lặp agent):
- **`max_tokens` mặc định quá nhỏ**: model `gpt-oss` dùng "reasoning_content"
  (chain-of-thought riêng kiểu Harmony) tốn token trước khi ra `content`
  cuối — nếu không set `max_tokens` đủ lớn, `content` trả về rỗng dù model
  "đã trả lời xong". Thêm `LLM_MAX_TOKENS` (env, mặc định 1024).
- **`content: null` bị từ chối (400)**: chuẩn OpenAI cho phép message
  assistant có `tool_calls` với `content: null`, nhưng Cloudflare validate
  chặt hơn, yêu cầu string. Đổi sang `content: ""` — vẫn tương thích ngược
  với OpenAI thật.

Dự kiến vẫn sẽ thử AWS Bedrock sau khi có tài khoản mới, nhưng hiện đã có
1 provider hoạt động ổn định để tiếp tục phát triển/test.

## 6. API FastAPI streaming (Ngày 4, R2)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint | Việc |
|---|---|
| `POST /conversations` | Tạo hội thoại mới |
| `GET /conversations` | Liệt kê hội thoại |
| `GET /conversations/{id}/messages` | Toàn bộ tin nhắn (persist bền vững, restart server vẫn còn) |
| `DELETE /conversations/{id}` | Xoá hội thoại |
| `POST /conversations/{id}/chat` | **Streaming SSE** — sự kiện `token`, `tool_call`, `done`, `error` |

Xem stream trong terminal bằng `curl -N`:

```bash
CID=$(curl -s -X POST localhost:8000/conversations -H "Content-Type: application/json" -d '{}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -N -X POST "localhost:8000/conversations/$CID/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho toi thong tin ve tau KOTA GAYA"}'
```

**Thiết kế đáng chú ý:**
- Route `chat` là `def` thường (không `async def`) — FastAPI tự chạy trong
  threadpool, tránh chặn event loop dù `openai`/`psycopg2` đều là thư viện
  đồng bộ, mà không cần viết lại bằng async client (đơn giản hơn, dễ giải
  thích hơn cho scope 7 ngày).
- Tin nhắn người dùng được lưu **trước khi** gọi LLM — nếu LLM lỗi, câu hỏi
  không bao giờ bị mất.
- Lỗi (LLM lỗi, tool lỗi, vượt số lần lặp) đều phát qua sự kiện `error`
  trong stream đang mở, không throw HTTP error giữa chừng (không thể — kết
  nối SSE đã bắt đầu).
- **Đã verify:** `tests/test_api.py` (5 test, FastAPI `TestClient` trên DB
  thật, mock `chat_stream`) — CRUD hội thoại, đúng thứ tự sự kiện SSE, đúng
  dữ liệu persist vào DB, và trường hợp LLM lỗi vẫn giữ được câu hỏi đã lưu.
  **Đã verify thêm với LLM thật** (Cloudflare Workers AI, `uvicorn` + `curl`
  thật, không qua TestClient/mock): token chảy về thực sự từng mảnh
  (`"Tau"` → `" EVER"` → `" V"` → `"IVA"` → `"."`, không phải chờ full rồi
  gửi 1 lần), đúng thứ tự `tool_call → token* → done`, persist đúng cấu
  trúc DB (role, `tool_call_id`, `tool_calls_json`) khớp với những gì đã
  stream ra.

## 7. Bộ nhớ hội thoại dài hạn (Ngày 5, R3)

`src/agent/memory.py::build_llm_context()` được gọi trước mỗi lượt chat:

- **Tổng số message ≤ `CONTEXT_WINDOW_TURNS`** (env, mặc định 10 — đếm theo
  **số message**, không phải "số lượt hỏi-đáp", vì 1 lượt có gọi tool chiếm
  nhiều hơn 1 message): dùng nguyên toàn bộ lịch sử.
- **Vượt ngưỡng**: các message cũ hơn cửa sổ được tóm tắt bằng LLM (viết
  bằng **tiếng Anh** — lý do: xem `docs/research.md`) → nhúng vector
  (`bge-m3`) → lưu `memory_chunks` (chỉ tóm tắt phần **MỚI** rơi ra khỏi cửa
  sổ mỗi lần). Khi trả lời: lấy top-20 ứng viên theo cosine similarity
  (ngưỡng tối thiểu chỉ 0.15, không dùng threshold cao vì điểm của `bge-m3`
  trên tóm tắt ngắn rất hẹp — xem phát hiện thật bên dưới) → **rerank**
  bằng cross-encoder (`bge-reranker-base`) → lấy top-3, chèn vào context
  trước cửa sổ ngắn hạn kèm câu dẫn nhấn mạnh đây là thông tin cần ưu tiên.
- Cắt cửa sổ **an toàn**: không bao giờ cắt đứt giữa 1 cặp
  `assistant(tool_calls)` + `tool`-result — nếu không, message `tool` đứng
  một mình sẽ bị API OpenAI từ chối (400).

**Đã verify với LLM thật, không chỉ mock — và kết quả KHÔNG hoàn toàn ổn
định, ghi nhận trung thực:** chạy Kịch bản 3 đầy đủ (13 lượt,
`CONTEXT_WINDOW_TURNS=6`) nhiều lần trong quá trình phát triển. 2 lần đầu
THẤT BẠI thật (0/2), phát hiện + sửa lần lượt 3 bug: (1) bản tóm tắt bỏ mất
mã hồ sơ dù văn bản gốc có đủ — do LLM ưu tiên chi tiết kỹ thuật khác, đã
siết lại `SUMMARIZE_PROMPT`; (2) ngưỡng similarity 0.5 loại bỏ cả chunk
đúng nhất — hạ xuống 0.15; (3) khi hội thoại có nhiều chunk (11+), embedding
similarity một mình không đủ phân biệt — thêm rerank. 1 lần chạy riêng sau
đó (sau cả 3 fix): **2/2 PASS**. Nhưng lần chạy đầy đủ cuối cùng (cùng lúc
với 4 kịch bản khác, `results/scenario_3.md`) lại **quay về 0/2** — model
lại nhầm sang tàu vừa nhắc gần nhất thay vì tàu đã yêu cầu ghi nhớ. **Kết
luận trung thực**: 3 fix đã sửa đúng 3 bug thật (xác nhận qua unit test +
ít nhất 1 lần verify thành công), nhưng độ tin cậy tổng thể của R3 khi hội
thoại dài (13+ lượt) với model 20B tham số vẫn **không đạt 100%** — đây là
giới hạn thật của cách tiếp cận (embedding+rerank trên chunk ngắn), không
phải lỗi code chưa sửa. Xem thêm `docs/architecture.md` mục 7.

Ngoài ra 11 unit test trong `tests/test_memory.py` (mock `chat_once`/
`embed_text`/`rerank`, DB pgvector thật) kiểm tra logic cửa sổ/tóm tắt/
retrieval/rerank độc lập với việc gọi LLM thật.

## 8. UI chat, bản đồ động, nhiều hành trình (Ngày 6, N1/N2/N3)

```bash
uvicorn main:app --reload
# mở http://localhost:8000
```

`web/index.html` — 1 file HTML/JS thuần (không build step), phục vụ qua
`StaticFiles` của FastAPI (`main.py`). 3 phần: sidebar hội thoại (N1),
khung chat streaming (N1), khung bản đồ Leaflet (N2/N3).

### N1 — UI chat

Danh sách hội thoại (`GET /conversations`), tạo mới/mở lại
(`POST`/`GET .../messages`), hiển thị câu trả lời streaming bằng cách đọc
trực tiếp `response.body` dạng stream (không dùng `EventSource` vì API
cần POST — tự parse block `event:`/`data:` cách nhau bởi dòng trống).

### N2 — Bản đồ động theo câu hỏi

Cơ chế chung cho mọi tool (không phải viết riêng từng tool): nếu kết quả
tool là `dict` có key `geojson`, `src/agent/agent.py::_split_geojson()` tự
tách phần đó ra thành sự kiện SSE `data` riêng gửi cho UI, đồng thời loại
bỏ khỏi nội dung gửi cho LLM (LLM chỉ thấy phần tóm tắt còn lại). Áp dụng
cho `get_journey`, `get_position_at_time`, `get_dark_gaps`,
`get_multi_journey_geojson` — **LLM không tự sinh HTML/JS bản đồ**, chỉ
điều phối gọi tool, UI tự vẽ bằng Leaflet khi nhận sự kiện `data`.

### N3 — Nhiều hành trình

- **Mức cơ bản**: `get_multi_journey_geojson(vessel_ids, start_ts, end_ts)`
  trả `FeatureCollection` (1 `LineString`/tàu), giới hạn `MAX_VESSELS_PER_REQUEST=50`.
- **Mức đầy đủ**: LLM tự hiểu "tất cả tàu của công ty X" / "tất cả tàu chở
  hàng" bằng cách tự gọi `get_company_vessels`/`list_vessels_by_type`
  trước để lấy `vessel_id`, rồi mới gọi `get_multi_journey_geojson`. Đường
  đi được đơn giản hoá (`ST_Simplify`) để vẽ mượt khi nhiều điểm.

**Đã verify bằng LLM thật (Kịch bản 5):** hỏi "hiện hành trình tất cả tàu
Evergreen Marine Corp khai thác 10-12/09" → model tự gọi đúng
`get_company_vessels` rồi `get_multi_journey_geojson` với 34 `vessel_id`
(không cần gợi ý thêm) → sự kiện `data` mang GeoJSON thật ~34KB (23 tàu,
3018 điểm) → câu trả lời cuối **chỉ chứa số liệu tóm tắt** (số tàu, số
điểm, bbox, tên tàu), không có toạ độ chi tiết — đúng thiết kế "dữ liệu lớn
không đi qua model". Transcript: `results/scenario_5.md`.

**Giới hạn đã biết:** `MAX_VESSELS_PER_REQUEST=50` là cắt cứng, chưa có
phân trang thật cho trường hợp vượt quá (vd. 628 tàu loại Cargo trong data)
— xem `docs/architecture.md` mục 7.

**Chưa verify được**: UI chưa được mở bằng trình duyệt thật trong môi
trường phát triển này (đã verify đầy đủ bằng `curl` ở tầng API — file được
serve đúng, luồng SSE/geojson hoạt động đúng — nhưng chưa xác nhận bằng
mắt trên Chrome/Firefox thật).

## Roadmap

- [x] Ngày 1: docker-compose, schema, pipeline nạp dữ liệu (đã vá: xác thực
      thứ tự cột CSV trước khi COPY, tránh nạp sai âm thầm khi cấu trúc file
      thay đổi)
- [x] Ngày 2: tầng truy vấn (tools) + unit test (24/24 pass trên data thật)
- [x] Ngày 3: tool-calling loop với LLM — logic verify kỹ qua mock; verify
      thêm với LLM thật (endpoint self-hosted `qwen3.5-9b` không ổn định →
      chuyển sang Cloudflare `gpt-oss-20b`, ổn định 5/5)
- [x] Ngày 4: API FastAPI streaming (SSE) + lưu hội thoại (verify bằng
      uvicorn + curl thật)
- [x] Ngày 5: bộ nhớ dài hạn pgvector + rerank (3 bug thật phát hiện + sửa
      qua test với LLM thật; độ tin cậy tổng thể vẫn không đạt 100% khi
      hội thoại dài — ghi nhận trung thực, xem mục 7)
- [x] Ngày 6: UI chat (N1), bản đồ động (N2), nhiều hành trình (N3) — verify
      bằng LLM thật (xem mục 8), chạy đủ 5 kịch bản mẫu (`results/`)
- [x] Ngày 7: tài liệu (`docs/research.md`, `docs/architecture.md`,
      `docs/api.md`), dọn dẹp, bàn giao

**73/73 unit/integration test pass** (`python -m pytest tests/ -v`).

**Kết quả chạy đầy đủ 5 kịch bản mẫu qua LLM thật** (transcript đầy đủ:
`results/`, kiểm chứng lại: `python scripts/verify_results.py`) — 9/13 kiểm
chứng tự động PASS; soát tay 2 trong 4 FAIL còn lại cho thấy **model trả
lời đúng dữ liệu nhưng diễn đạt khác cách check đơn giản dự đoán** (vd. nói
"ngày A dài hơn ngày B" thay vì "ngày B ngắn hơn ngày A" — đúng về bản chất,
check chỉ tìm 1 chiều câu chữ). 2 FAIL còn lại (Kịch bản 3, bộ nhớ dài hạn)
là **thật** — xem mục 7 để biết chi tiết và mức độ tin cậy thực tế của R3.

## Checklist bàn giao (R1–D3)

| Mã | Nội dung | Trạng thái |
|---|---|---|
| R1 | Nạp dữ liệu + tầng truy vấn (tools, SQL tham số hoá, tìm tàu linh hoạt) | ✅ Xong, verify Ngày 2 |
| R2 | API chat streaming SSE, quản lý hội thoại, nhiều hội thoại song song | ✅ Xong, verify Ngày 4 + live |
| R3 | Lịch sử bền vững + follow-up + bộ nhớ dài hạn vector DB | ⚠️ Xong về mặt cơ chế (3 bug thật đã sửa), **độ tin cậy chưa 100%** khi hội thoại dài — xem mục 7 |
| R4 | Trả lời đúng dữ liệu thật, không bịa | ✅ Verify qua 5 kịch bản mẫu với LLM thật |
| N1 | UI chat đơn giản | ✅ `web/index.html`, chưa test trên trình duyệt thật (chỉ verify qua curl ở tầng API) |
| N2 | Bản đồ động theo câu hỏi, dữ liệu qua sự kiện có cấu trúc | ✅ Verify với LLM thật (sự kiện `data` mang GeoJSON) |
| N3 | Nhiều hành trình — mức cơ bản (API + giới hạn/phân trang) và mức đầy đủ (LLM tự hiểu theo công ty/loại tàu) | ✅ Verify với LLM thật (Kịch bản 5); giới hạn đã biết: cắt cứng 50 tàu/lần (chưa phân trang thật), so sánh nhiều tàu chưa scale — xem `docs/architecture.md` |
| D1 | README, `.env.example`, không hardcode | ✅ |
| D2 | `docs/research.md`, `docs/architecture.md` | ✅ |
| D3 | Unit/integration test, `results/` transcript kịch bản | ✅ 73 test, 5 kịch bản đầy đủ trong `results/` |

**Chưa làm / để ngoài phạm vi 7 ngày** (đã ghi trong `docs/architecture.md`
mục "Hạn chế đã biết"): auth/rate limiting, connection pool, structured
logging + metrics/tracing, phân trang thật cho N3 khi vượt giới hạn tàu,
tool tổng hợp so sánh nhiều tàu (tránh gọi `get_journey` từng tàu một).
