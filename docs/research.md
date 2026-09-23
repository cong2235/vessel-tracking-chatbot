# Nghiên cứu và lựa chọn công nghệ

## 0. Phương pháp và tiêu chí đánh giá

Tài liệu này ghi lại **quá trình** đi đến lựa chọn cuối, không chỉ kết quả —
gồm cả phương án đã cân nhắc trên giấy nhưng không chọn, phương án đã thử
nghiệm thật và thất bại, và root-cause của từng lần thất bại đó. Nguyên tắc
xuyên suốt: **chỉ ghi là "đã verify" khi có bằng chứng thật** (log, transcript,
số liệu đo được) — phần nào chỉ là suy luận trên tài liệu công khai của nhà
cung cấp (chưa tự tay test) được đánh dấu rõ "cân nhắc trên giấy".

Tiêu chí đánh giá dùng chung cho mọi lựa chọn, xếp theo trọng số ưu tiên cho
bài toán cụ thể này (không phải trọng số chung cho mọi hệ thống):

| Tiêu chí | Vì sao quan trọng ở bài này |
|---|---|
| **Độ tin cậy tool-calling** | R4 yêu cầu "không bịa" — nếu model không trigger đúng cơ chế `tool_calls` chuẩn, toàn bộ pipeline mất tác dụng, model tự bịa câu trả lời |
| **Hỗ trợ tiếng Việt** | Người dùng hỏi tiếng Việt, dữ liệu gốc (nhãn loại tàu) là tiếng Anh — cần model/embedding xử lý tốt cả hai |
| **Chi phí ở quy mô bài test** | Vài trăm lượt hỏi khi chấm — ngân sách cá nhân, không phải ngân sách doanh nghiệp |
| **Độ phức tạp hạ tầng** | Deadline 7 ngày, một mình triển khai — ưu tiên ít moving part |
| **Khả năng giải thích được** | Đề bài yêu cầu tường minh "phải giải thích được mọi phần trong tài liệu mô tả" dù có dùng framework/AI hỗ trợ |

## 1. LLM

### 1.1. Các ứng viên đã cân nhắc

| Model | Loại | Cân nhắc trên giấy | Lý do không chọn / không test |
|---|---|---|---|
| GPT-4o-mini / GPT-4.1-mini (OpenAI) | API trả phí | Tool-calling rất ổn định, context 128K, giá rẻ trong nhóm managed API | Không test trực tiếp — cần tài khoản OpenAI riêng, ưu tiên thử trước 1 model open-weight để so sánh chi phí/độ ổn định thực tế trước khi quyết định trả phí cho provider đóng |
| Claude Haiku (Anthropic) | API trả phí | Tool-calling tốt, mạnh về việc bám sát instruction (phù hợp yêu cầu "không bịa" nghiêm ngặt của R4) | Tương tự — không có tài khoản sẵn trong thời gian làm bài, để dành hướng mở rộng |
| Gemini Flash (Google) | API trả phí | Giá rẻ, context dài | Ít kinh nghiệm với function-calling schema của Gemini (khác cấu trúc OpenAI), rủi ro tốn thời gian debug format thay vì debug logic |
| Qwen2.5/3.5 (self-host qua vLLM) | Model mở | Miễn phí (chỉ tốn compute tự host), hỗ trợ tiếng Việt khá tốt | **Đã test thật — xem 1.2, thất bại vì lý do hạ tầng inference, không phải lý do model** |
| Llama 3.1/3.3 (self-host) | Model mở | Cộng đồng lớn, nhiều tool hỗ trợ | Không test — cùng nhóm rủi ro hạ tầng tự host như Qwen, ưu tiên thời gian cho hướng managed-inference của model mở (Cloudflare Workers AI) thay vì tự vá vLLM |
| `gpt-oss-20b`/`gpt-oss-120b` (OpenAI, open-weight) | Model mở, chạy qua managed inference | Thiết kế riêng cho agentic tool-calling (định dạng Harmony có channel suy luận riêng), context 128K | **Đã test thật — xem 1.2, lựa chọn cuối cùng** |
| DeepSeek-V3 | Model mở | Chi phí cực rẻ, benchmark công khai tốt | Không có sẵn qua managed-inference provider đã dùng (Cloudflare) tại thời điểm làm bài, không đủ thời gian dựng thêm 1 hạ tầng inference riêng |

**Kết luận thu hẹp**: giữa các lựa chọn managed-API đóng phí (OpenAI/Anthropic/
Gemini — nhiều khả năng ổn định nhưng chưa kiểm chứng) và model mở tự
host/managed-inference (rẻ hơn nhưng rủi ro tool-calling chưa rõ), quyết định
**test trực tiếp 2 phương án ở cực rẻ nhất** trước (self-host Qwen vs managed
gpt-oss) để có dữ liệu thật về độ ổn định, thay vì chọn OpenAI mặc định theo
quán tính — đúng tinh thần "phải giải thích được" mà đề bài yêu cầu: mọi lựa
chọn đều có bằng chứng, không phải "vì ai cũng dùng GPT".

### 1.2. Thử nghiệm thật: `qwen3.5-9b` (self-host) vs `gpt-oss-20b` (Cloudflare)

**Phương pháp thử nghiệm**: cùng 1 câu hỏi cố định — *"Cho tôi thông tin về
tàu KOTA GAYA"* (trigger đúng 1 tool call `search_vessel`) — gọi lặp lại 5
lần độc lập ở `temperature=0` cho mỗi model, qua đúng 1 đường code
(`src/agent/agent.py::run_agent_turn`, không đổi gì giữa 2 lần thử ngoài
`OPENAI_BASE_URL`/`OPENAI_CHAT_MODEL`). Tiêu chí PASS: model trả về đúng
trường `tool_calls` chuẩn của OpenAI Chat Completions API (không phải model
tự in ra text có dạng giống lời gọi hàm).

| Model | Hạ tầng | Kết quả (5 lần lặp) | Ghi chú |
|---|---|---|---|
| `qwen3.5-9b` | Self-host qua vLLM, endpoint nội bộ | **0/5** | Model in tool-call dưới dạng text thô `<tool_call> search_vessel(...)` thay vì field `tool_calls` |
| `@cf/openai/gpt-oss-20b` | Cloudflare Workers AI (managed) | **5/5** | Trigger đúng `tool_calls` mọi lần, câu trả lời khớp 100% dữ liệu thật (đối chiếu tay) |

**Root-cause phân tích cho `qwen3.5-9b`**: nghi vấn hàng đầu là server vLLM
thiếu cấu hình `--tool-call-parser hermes` (Qwen dùng định dạng function-call
riêng trong chat template, vLLM cần parser tương ứng để bóc tách thành
`tool_calls` chuẩn OpenAI — nếu thiếu, toàn bộ nội dung rơi thẳng vào
`content` dạng text). Đây là **lỗi cấu hình hạ tầng inference tự host**, không
phải lỗi năng lực model hay lỗi vòng lặp tool-calling của hệ thống (vòng lặp
đã được test riêng, kỹ, bằng mock — xem `README.md` mục 5). Hệ quả thực tế
khi lỗi này xảy ra: code (đúng thiết kế) coi `content` trả về là câu trả lời
cuối cùng — không tool nào chạy — model tự bịa phần còn lại từ kiến thức
chung, **vi phạm trực tiếp R4**. Đây chính là lý do quyết định không cố sửa
tiếp hạ tầng vLLM trong quỹ thời gian 7 ngày mà chuyển hẳn sang managed
inference.

**Lý do chọn `gpt-oss-20b` (ngoài kết quả test):**
- Model do chính OpenAI phát hành dạng open-weight, thiết kế riêng cho
  agentic tool-calling (định dạng Harmony có channel suy luận riêng).
- Giá rẻ ($0.2 / $0.3 mỗi triệu token input/output theo bảng giá Cloudflare
  Workers AI tại thời điểm viết tài liệu), context 128K.
- Có sẵn qua Cloudflare Workers AI — không cần tự host, không cần lo hạ tầng
  GPU, và API tương thích chuẩn OpenAI Chat Completions nên không cần viết
  code riêng cho provider này (đổi 3 biến môi trường, không đổi 1 dòng code).

### 1.3. Các quirk phát hiện qua test thật (không phải giả định)

| # | Vấn đề | Triệu chứng | Nguyên nhân | Cách khắc phục | File |
|---|---|---|---|---|---|
| 1 | `max_tokens` mặc định quá nhỏ | `content` rỗng dù `finish_reason="length"`, model "trả lời xong" nhưng không ra chữ | `gpt-oss` dùng `reasoning_content` (chain-of-thought riêng kiểu Harmony) tốn hết ngân sách token trước khi ra `content` cuối | Thêm biến môi trường `LLM_MAX_TOKENS`, nâng mặc định 1024 → 4096 sau khi test câu hỏi N3 nhiều bước | `src/utils/config.py::get_max_tokens` |
| 2 | `content: null` bị từ chối (HTTP 400) | Request lỗi khi message `assistant` có `tool_calls` | Chuẩn OpenAI cho phép `content: null` cho message có `tool_calls`, nhưng Cloudflare validate chặt hơn, yêu cầu string | Đổi sang `content: ""` — vẫn tương thích ngược với OpenAI thật | `src/models/llm_client.py` |
| 3 | Rò rỉ token định dạng nội bộ vào tên tool | Tool gọi ra có tên dạng `get_vessel_info<|channel|>analysis` | Cơ chế phân tách channel suy luận/nội dung của Harmony đôi khi lẫn vào output tên hàm | Không sửa ở tầng model — tận dụng cơ chế có sẵn "tool không tồn tại → trả lỗi cho model" (`agent.py::_execute_tool`), model tự phục hồi và gọi lại đúng tên ở lượt sau; tốn 1 vòng lặp nhưng không crash | `src/agent/agent.py::_execute_tool` |
| 4 | Lặp tham số 2 lần trong 1 lời gọi tool | Model gọi `vessel_ids: [id1, id1]` thay vì 1 lần | Không rõ nguyên nhân sâu (có thể do decode lặp ở tầng streaming của provider) | Không cần sửa — SQL các tool đã dùng `GROUP BY`/`ANY()` nên trùng lặp không ảnh hưởng kết quả, chỉ lãng phí token | — |
| 5 | Lỗi `500 Internal Server Error` thoáng qua | 1 lần chạy `scripts/run_scenarios.py` bị crash giữa chừng | Hạ tầng inference dùng chung/giá rẻ của Cloudflare không đảm bảo 100% uptime cho mọi request | Thêm retry (`tenacity`, 3 lần, backoff tăng dần) — chỉ retry lỗi 5xx/mất kết nối, không retry lỗi 4xx (request sai thì thử lại vẫn sai) | `src/models/llm_client.py::_create_completion` |

**Lưu ý thật, không tô hồng**: ở 1 lần chạy khác (Kịch bản 5, lượt 2–3,
`results/scenario_5.md`), lỗi 500 kéo dài **hơn cả 3 lần retry** (~10s) — đây
là rủi ro vận hành thật của việc dùng hạ tầng inference dùng chung/giá rẻ,
không phải lỗi code. Production thật cần thêm alerting + có thể cần fallback
sang provider khác khi 1 provider downtime kéo dài, việc này nằm ngoài phạm
vi 7 ngày (xem `docs/architecture.md` mục "Hạn chế đã biết").

## 2. Embedding

### 2.1. Các ứng viên đã cân nhắc

| Model | Đa ngôn ngữ? | Chiều | Ghi chú |
|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | Có, nhưng tối ưu chính cho tiếng Anh | 1536 | Lựa chọn mặc định ban đầu trong `.env.example` (giữ để tương thích khi dùng OpenAI thật) — yêu cầu tài khoản OpenAI riêng với LLM đang test |
| `bge-base-en-v1.5` | Không (thuần tiếng Anh) | 768 | Loại ngay — nội dung tóm tắt hội thoại gốc có thể lẫn tiếng Việt |
| `multilingual-e5-large` | Có | 1024 | Cân nhắc trên giấy, không test — không có sẵn qua cùng provider (Cloudflare) đang dùng cho LLM, thêm 1 provider = thêm 1 API key/1 điểm lỗi |
| Cohere `embed-multilingual-v3` | Có | 1024 | Cân nhắc trên giấy — chất lượng đa ngôn ngữ tốt theo tài liệu công khai, nhưng thêm nhà cung cấp thứ 3 không cần thiết ở quy mô bài test |
| **`@cf/baai/bge-m3`** (Cloudflare) | **Có, hỗ trợ tiếng Việt** | **1024** | **Đã chọn** |

**Lý do chọn `bge-m3`**: đa ngôn ngữ thật (không chỉ tiếng Anh + dịch máy),
cùng provider với LLM đang dùng (1 API key, 1 hoá đơn, không thêm điểm lỗi hạ
tầng) — đúng nguyên tắc "ít moving part" đặt ra ở mục 0.

### 2.2. Phát hiện quan trọng qua test thật: similarity thấp và hẹp trên tóm tắt ngắn

**Phương pháp**: trong quá trình phát triển R3, đo cosine similarity
(`1 - (embedding <=> query)` qua pgvector) giữa câu hỏi follow-up thật và các
`memory_chunks` đã tóm tắt (dưới 150 từ/chunk) trong nhiều lượt chạy Kịch bản
3. Quan sát: **kể cả giữa câu hỏi và đoạn tóm tắt liên quan nhất**, điểm số
chỉ rơi vào khoảng **0.24–0.35** trên thang 0–1 — hẹp hơn nhiều so với trực
giác thường gặp khi dùng embedding OpenAI (nơi ngưỡng ~0.7–0.8 thường được
coi là "liên quan").

**Hệ quả và cách xử lý**: ngưỡng tuyệt đối ban đầu đặt `0.5` (theo trực giác
kiểu OpenAI) **lọc mất cả kết quả đúng nhất** — không phải do embedding tệ, mà
do thang điểm của `bge-m3` trên đoạn văn ngắn vốn hẹp hơn. Đã hạ xuống
`MEMORY_MIN_SIMILARITY = 0.15` (chỉ dùng để loại nhiễu rõ ràng) và chuyển
sang dựa vào **thứ hạng** (`ORDER BY ... LIMIT`) thay vì ngưỡng tuyệt đối làm
tiêu chí quyết định chính — chi tiết root-cause đầy đủ (3 bug liên quan) xem
mục 6.

## 3. Vector database

### 3.1. So sánh

| Lựa chọn | Ưu | Nhược | Khi nào nên dùng |
|---|---|---|---|
| **pgvector** (đã chọn) | Cùng Postgres đang dùng cho R1 (PostGIS) — không thêm service, không thêm kết nối, không thêm cơ chế đồng bộ dữ liệu giữa 2 hệ; đủ nhanh ở quy mô vài trăm–vài nghìn chunk/hội thoại; hỗ trợ index HNSW từ pgvector ≥ 0.5 | Không chuyên biệt cho vector search ở quy mô hàng chục triệu vector — thiếu các tối ưu như quantization, sharding ngang có sẵn của DB chuyên dụng | Dữ liệu ứng dụng đã ở Postgres, quy mô vector vừa/nhỏ, ưu tiên đơn giản hạ tầng |
| Qdrant | Index HNSW tối ưu hơn cho vector thuần, filter phong phú, dashboard quản trị tốt | Thêm 1 service, 1 kết nối, cần đồng bộ ID với DB chính | Hệ thống vector-first, hàng triệu+ vector, cần filter phức tạp |
| Milvus | Scale ngang tốt nhất trong nhóm, thiết kế cho tỷ vector | Vận hành phức tạp nhất (nhiều thành phần: proxy, query node, data node...) — quá mức cần thiết cho 1 ứng dụng chat | Quy mô rất lớn, đội vận hành riêng cho hạ tầng dữ liệu |
| Chroma | Rất dễ chạy local, phù hợp prototype nhanh | Không phải lựa chọn production-grade cho hàng triệu vector, hệ sinh thái vận hành (backup, HA) còn non | Prototype/demo cá nhân, không cần persist bền vững nghiêm ngặt |

**Lý do chọn pgvector**: dữ liệu tàu biển (R1) đã cần PostGIS trên Postgres;
dùng luôn pgvector trên CÙNG database giảm hẳn độ phức tạp hạ tầng, hợp lý
cho quy mô bài test (vài trăm–vài nghìn chunk mỗi hội thoại). Nếu quy mô lớn
hơn nhiều (hàng triệu vector, nhiều tenant), Qdrant/Milvus sẽ có lợi thế về
hiệu năng index chuyên biệt — ghi vào hướng mở rộng
(`docs/architecture.md` mục 9).

## 4. Reranker

### 4.1. So sánh

| Lựa chọn | Ghi chú |
|---|---|
| **`@cf/baai/bge-reranker-base`** (đã chọn) | Cross-encoder, cùng provider Cloudflare — không thêm API key |
| Cohere Rerank v3 | Cân nhắc trên giấy — chất lượng đa ngôn ngữ tốt theo tài liệu công khai, nhưng thêm nhà cung cấp thứ 3, không cần thiết khi `bge-reranker-base` đã đủ dùng sau khi đã xử lý được giới hạn ngôn ngữ (xem 4.2) |
| Cross-encoder `ms-marco-MiniLM` (self-host) | Cân nhắc trên giấy — miễn phí nhưng cần tự host thêm 1 service inference, đi ngược nguyên tắc "ít moving part" |

### 4.2. Phát hiện quan trọng qua test thật: reranker chỉ hoạt động tốt với tiếng Anh

**Phương pháp**: chạy cùng 1 tình huống truy xuất bộ nhớ (1 câu hỏi + 3 đoạn
văn ứng viên, trong đó chỉ 1 đoạn thật sự liên quan) bằng 2 phiên bản ngôn
ngữ — tiếng Anh và tiếng Việt — qua `bge-reranker-base`.

| Ngôn ngữ | Điểm đoạn đúng | Điểm 2 đoạn còn lại | Kết quả xếp hạng |
|---|---|---|---|
| Tiếng Anh | 0.62 | 0.0001 – 0.0003 | Đúng — đoạn liên quan xếp hạng 1 rõ rệt |
| Tiếng Việt (cùng nội dung, dịch tương đương) | — | — | **Sai** — đoạn đúng xếp hạng THẤP NHẤT trong 3 lựa chọn |

**Quyết định rút ra**: đổi `SUMMARIZE_PROMPT` (`src/agent/memory.py`) sang
yêu cầu LLM tóm tắt bằng **tiếng Anh**, mặc dù hội thoại gốc là tiếng Việt.
Điều này chấp nhận được vì `memory_chunks` chỉ là dữ liệu nội bộ cho LLM đọc
lại (không hiển thị trực tiếp cho người dùng) — đổi ngôn ngữ tóm tắt không
ảnh hưởng trải nghiệm vì câu trả lời cuối luôn bằng tiếng Việt theo
`SYSTEM_PROMPT`.

## 5. Framework agent

**Không dùng LangChain/LlamaIndex/LangGraph.** Tự viết vòng lặp tool-calling
(`src/agent/agent.py`, ~135 dòng cho cả bản thường và bản streaming).

| Lựa chọn | Ưu | Nhược | Quyết định |
|---|---|---|---|
| LangChain | Nhiều tool tích hợp sẵn, cộng đồng lớn | Nhiều lớp trừu tượng (`AgentExecutor`, `Runnable`...) — khó giải thích tường minh từng bước cho người chấm; version churn thường xuyên | Không dùng |
| LangGraph | Kiểm soát luồng tốt hơn LangChain thuần, phù hợp agent có nhánh phức tạp | Overhead học + giải thích lớn hơn nhiều so với lợi ích cho 1 luồng tuyến tính (gọi LLM → tool → lặp) | Không dùng |
| CrewAI/AutoGen (multi-agent) | Mạnh cho bài toán nhiều agent phối hợp | Bài toán này chỉ có 1 agent, 1 luồng — dùng framework multi-agent là thừa | Không dùng |
| **Tự viết vòng lặp** | Tường minh 100%, dễ debug (đã chứng minh qua việc tìm root-cause 3 bug R3 nhanh — có thể đặt breakpoint/log ở đúng dòng nghi ngờ), không phụ thuộc version của framework ngoài | Phải tự viết lại các tiện ích framework có sẵn (retry, streaming parser...) | **Đã chọn** |

**Lý do chọn (bám sát yêu cầu đề bài)**: đề bài ghi rõ *"phải giải thích được
mọi phần trong tài liệu mô tả"* dù được dùng framework/trợ lý AI. Với 9 tool
và luồng tuyến tính (gọi LLM → có tool_call thì chạy tool → đưa kết quả lại →
lặp), lợi ích của 1 framework agent nặng (orchestration phức tạp, đa agent,
graph có nhánh...) không cần thiết, trong khi chi phí phải giải thích được
toàn bộ lớp trừu tượng bên trong framework đó là có thật.

## 6. So sánh chiến lược bộ nhớ dài hạn (R3)

### 6.1. Ma trận so sánh

| Chiến lược | Độ chính xác dài hạn | Chi phí thêm | Độ trễ thêm | Độ phức tạp | Rủi ro thất bại |
|---|---|---|---|---|---|
| Cửa sổ trượt (sliding window) thuần | Rất thấp — mất hoàn toàn thông tin ngoài cửa sổ | Không | Không | Rất thấp | Cao khi hội thoại vượt cửa sổ (kịch bản 3 sẽ luôn fail) |
| Tóm tắt (summarization) thuần | Trung bình — phụ thuộc chất lượng tóm tắt, có thể bỏ sót chi tiết | Thấp (1 lần gọi LLM tóm tắt) | Thấp | Thấp | Model tóm tắt có thể bỏ sót đúng thông tin cần nhớ (đã gặp thật, xem 6.2 bug #1) |
| Truy xuất vector (embedding retrieval) thuần | Trung bình-cao, nhưng phụ thuộc chất lượng embedding | Trung bình (nhúng + query mỗi lượt) | Trung bình | Trung bình | Kém khi nhiều chunk ngắn/giống nhau cạnh tranh điểm số sát nhau (đã gặp thật, xem 6.2 bug #3) |
| Kết hợp (sliding window + tóm tắt + embedding + rerank) | Cao hơn từng phần riêng lẻ, nhưng **vẫn không đạt 100%** với model 20B khi hội thoại rất dài | Cao nhất (tóm tắt + nhúng + rerank mỗi lượt) | Cao nhất | Cao — nhiều điểm có thể lỗi | Đã gặp thật cả 3 bug (6.2) — mỗi lớp thêm vào giảm 1 loại lỗi nhưng làm hệ thống khó debug hơn |
| **Kết hợp + pin fact tường minh** (đã bổ sung sau review) | **Cao nhất trong các phương án đã thử** — tách riêng "yêu cầu ghi nhớ" khỏi "ngữ cảnh trôi nổi" | Thấp (chỉ thêm 1 regex + 1 cột boolean, không thêm lời gọi model) | Không đáng kể | Trung bình (thêm 1 nhánh logic, không thêm service) | Phụ thuộc regex trigger nhận diện đúng câu "ghi nhớ giúp tôi..." — xem giới hạn ở 6.3 |

### 6.2. Case study: 3 bug thật tìm được khi test R3 bằng LLM thật

Kiểm chứng bằng Kịch bản 3 (13 lượt, `CONTEXT_WINDOW_TURNS=6` khi test) —
**không chỉ mock, chạy thật nhiều lần trong quá trình phát triển**:

| # | Triệu chứng | Root cause | Cách sửa | Xác nhận |
|---|---|---|---|---|
| 1 | Bản tóm tắt bỏ mất mã hồ sơ (`HS-2026-117`) dù văn bản gốc có đủ | LLM tóm tắt ưu tiên chi tiết kỹ thuật khác (thông số tàu) xuất hiện cùng đoạn, bỏ qua câu "ghi nhớ giúp tôi..." vì không được nhấn mạnh trong prompt tóm tắt | Siết `SUMMARIZE_PROMPT`: yêu cầu rõ "nếu người dùng nói 'ghi nhớ', PHẢI liệt kê tường minh, không được bỏ qua vì ưu tiên chi tiết khác" | Unit test `tests/test_memory.py` + verify LLM thật |
| 2 | Ngưỡng similarity 0.5 loại bỏ cả chunk đúng nhất | Điểm cosine của `bge-m3` trên tóm tắt ngắn hẹp tự nhiên (0.24–0.35, xem mục 2.2) — ngưỡng 0.5 cao hơn cả điểm của chunk liên quan nhất | Hạ `MEMORY_MIN_SIMILARITY` xuống 0.15, chuyển sang dùng thứ hạng thay vì ngưỡng tuyệt đối | Verify LLM thật |
| 3 | Khi hội thoại có 11+ chunk cạnh tranh, embedding một mình không đủ phân biệt — chunk đúng bị loại khỏi top-3 | Nhiều chunk có điểm sát nhau (0.24–0.35) do bản chất thang điểm hẹp | Thêm rerank (cross-encoder `bge-reranker-base`) sau bước lọc similarity | 1 lần chạy độc lập đạt 2/2 sau fix — nhưng xem tiếp bên dưới |

**Kết quả sau cả 3 fix, ghi nhận trung thực**: 1 lần chạy riêng đạt 2/2 PASS,
nhưng 1 lần chạy đầy đủ khác (cùng lúc với 4 kịch bản còn lại) lại **quay về
0/2** — model nhầm sang tàu vừa nhắc gần nhất thay vì tàu đã yêu cầu ghi nhớ ở
lượt 1. Kết luận tại thời điểm đó: 3 fix đúng và cần thiết, nhưng **cơ chế
"kết hợp" thuần (tóm tắt + embedding + rerank) vẫn phụ thuộc vào việc model
20B tham số tự ưu tiên đúng ngữ cảnh trong 1 khối văn bản dài** — đây là giới
hạn xác suất, không phải bug có thể sửa dứt điểm bằng cách chỉnh tham số.

### 6.3. Giải pháp bổ sung sau review: pin fact tường minh

Thay vì tiếp tục tinh chỉnh tham số của cơ chế "kết hợp" (vốn đã chạm giới
hạn ở 6.2), hướng sửa được chọn là **tách riêng lớp "yêu cầu ghi nhớ tường
minh" ra khỏi lớp "tóm tắt ngữ nghĩa nói chung"**:

- Khi 1 message của user khớp regex nhận diện câu "ghi nhớ" (`ghi nho|nho
  giup|nho ho|hay nho|nho rang`, so khớp trên bản không dấu để bắt cả 2 dạng
  có dấu/không dấu), toàn văn message đó được lưu thành **1 fact riêng**
  (`memory_chunks.is_pinned = true`), **không** đi qua bước tóm tắt của LLM.
- Khi dựng context cho lượt tiếp theo, mọi fact có `is_pinned = true` của
  hội thoại đó **luôn được đưa vào**, không phụ thuộc điểm similarity/rerank
  — loại bỏ hoàn toàn nguyên nhân gốc của bug #2 và #3 (ngưỡng điểm, cạnh
  tranh giữa nhiều chunk) cho đúng loại thông tin quan trọng nhất.
- Đánh đổi: cơ chế regex chỉ bắt được câu nói theo mẫu tường minh
  ("ghi nhớ giúp tôi...") — nếu người dùng diễn đạt cách khác hoàn toàn mà
  không dùng các từ khoá trên, fact đó vẫn đi qua đường tóm tắt ngữ nghĩa
  thông thường (mục 6.1, dòng "Kết hợp"), với độ tin cậy như đã ghi nhận ở
  6.2. Đây là đánh đổi có chủ đích: ưu tiên độ chính xác gần như tuyệt đối
  cho đúng use case được nêu rõ trong kịch bản mẫu của đề bài (Kịch bản 3,
  lượt 1: *"Ghi nhớ giúp tôi: tôi phụ trách hồ sơ..."*), chấp nhận rủi ro dư
  thấp hơn ở use case không nằm trong phạm vi kịch bản mẫu.

**Kết quả sau khi thêm cơ chế pin**: chạy lại đầy đủ 5 kịch bản mẫu qua LLM
thật, kiểm chứng bằng `scripts/verify_results.py` — Kịch bản 3 lượt 12 và 13
**PASS** (transcript: `results/scenario_3.md`), tổng thể **13/13 (100%)**
kiểm chứng tự động trên cả 5 kịch bản (`results/verify_summary.txt`). Ghi
chú trung thực: đây là kết quả của 1 lần chạy đầy đủ; do bản chất không xác
định của LLM, không có gì đảm bảo 100% ở MỌI lần chạy — nhưng khác với cơ chế
"kết hợp" thuần (phụ thuộc hoàn toàn vào lựa chọn ngữ cảnh của model), cơ chế
pin loại bỏ hẳn 1 lớp bất định (điểm similarity/rerank) cho đúng loại câu hỏi
mà kịch bản mẫu kiểm tra, nên kỳ vọng ổn định hơn hẳn về mặt lý thuyết.

## 7. Framework backend

**FastAPI + PostgreSQL/PostGIS + Docker Compose** — theo đúng gợi ý của đề
bài. Vài điểm cân nhắc thêm không có trong gợi ý gốc:

| Quyết định | Lý do |
|---|---|
| SSE (`StreamingResponse`) thay vì WebSocket | Giao tiếp chat ở đây về bản chất **1 chiều theo lượt** (client gửi 1 message, server trả về 1 luồng sự kiện rồi đóng) — không cần kênh 2 chiều liên tục của WebSocket. SSE đơn giản hơn (không cần quản lý handshake/ping-pong riêng), FastAPI hỗ trợ tốt qua `StreamingResponse`, và debug được bằng `curl -N` thuần (yêu cầu D1) mà không cần client WebSocket riêng |
| PostgreSQL + PostGIS thay vì MongoDB/Elasticsearch cho dữ liệu không gian | PostGIS là lựa chọn tiêu chuẩn ngành cho dữ liệu địa lý quan hệ (index GiST, hàm `ST_*` phong phú, hỗ trợ `geography` cho tính khoảng cách chính xác trên mặt cầu) — MongoDB geo-index đơn giản hơn nhưng thiếu các phép tính hình học phức tạp (`ST_Simplify`, `ST_MakeLine` có `ORDER BY`) mà N2/N3 cần |
| 1 database cho cả dữ liệu tàu biển + hội thoại + vector | Xem mục 3 — giảm số lượng service cần vận hành trong 7 ngày |

## 8. Bảng tổng hợp lựa chọn cuối

| Thành phần | Lựa chọn | Lý do 1 dòng |
|---|---|---|
| LLM | `gpt-oss-20b` qua Cloudflare Workers AI | Duy nhất đạt 5/5 tool-calling ổn định trong 2 phương án đã test thật |
| Embedding | `bge-m3` | Đa ngôn ngữ thật, cùng provider với LLM |
| Vector DB | pgvector (trên Postgres sẵn có) | Không thêm service, đủ nhanh ở quy mô bài test |
| Reranker | `bge-reranker-base` (tóm tắt ép tiếng Anh) | Cross-encoder phân biệt tốt hơn embedding đơn thuần, nhưng cần tóm tắt tiếng Anh để hoạt động đúng |
| Chiến lược bộ nhớ | Kết hợp (sliding window + tóm tắt + embedding + rerank) **+ pin fact tường minh** | Phương án duy nhất đạt 13/13 kịch bản mẫu khi kiểm chứng bằng LLM thật |
| Framework agent | Tự viết (~135 dòng) | Bám sát yêu cầu "phải giải thích được mọi phần" |
| Backend | FastAPI + SSE + PostgreSQL/PostGIS + Docker Compose | Đúng gợi ý đề bài, SSE đủ cho giao tiếp 1 chiều theo lượt |
