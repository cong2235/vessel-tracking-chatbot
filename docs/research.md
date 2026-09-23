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

### 1.4. Chuyển sang `gpt-4o-mini` (OpenAI thật) sau khi gặp giới hạn hạ tầng

**Sự cố thật dẫn đến quyết định đổi**: giữa quá trình chạy lại 5 kịch bản
mẫu để kiểm chứng các bản sửa, tài khoản Cloudflare Workers AI báo lỗi
`429 — you have used up your daily free allocation of 10,000 neurons`.
Đây đúng là rủi ro đã cảnh báo ở mục 1.3 ("hạ tầng inference dùng chung/giá
rẻ không đảm bảo uptime") — nhưng lần này chặn đứng hoàn toàn việc test,
không chỉ làm chậm 1 request. Quyết định: tách riêng "chọn theo hạ tầng có
sẵn" khỏi "chọn theo chi phí + độ phù hợp thuần" — nếu bỏ qua yếu tố hạ
tầng, phương án hợp lý nhất là dùng thẳng OpenAI thật, vì `src/models/
llm_client.py` vốn viết đúng chuẩn OpenAI Chat Completions gốc (không phải
bản Cloudflare giả lập) — đổi provider không cần sửa 1 dòng code nào cho
phần gọi LLM.

**Phát hiện thật khi đổi (bug hạ tầng, không phải bug logic)**: để lại dòng
`OPENAI_BASE_URL=` (rỗng) trong `.env` — đúng theo hướng dẫn cũ của
`.env.example` ("bỏ trống để dùng OpenAI mặc định") — khiến OpenAI SDK báo
lỗi `UnsupportedProtocol: Request URL is missing an 'http://' or 'https://'
protocol`. Nguyên nhân: SDK tự đọc thẳng biến môi trường `OPENAI_BASE_URL`
từ `os.environ`, và một biến **rỗng nhưng tồn tại** khác với **biến không
tồn tại** — `os.environ.get("OPENAI_BASE_URL", DEFAULT)` trả về `""` (vì
key có tồn tại) chứ không trả về `DEFAULT`. Việc `src/utils/config.py::
get_openai_base_url()` tự chuyển `"" -> None` không đủ, vì SDK đọc thẳng
biến môi trường ở tầng của chính nó, không qua hàm này. Đã sửa 2 lớp:
xoá hẳn biến rỗng khỏi `os.environ` trước khi khởi tạo client
(`src/models/llm_client.py::get_client`) + cập nhật hướng dẫn trong
`.env.example` khuyến cáo xoá hẳn dòng thay vì để rỗng. Thêm 1 unit test
hồi quy (`tests/test_llm_client_retry.py::test_get_client_ignores_empty_string_base_url_env_var`).

**So sánh chất lượng suy luận thật giữa `gpt-oss-20b` và `gpt-4o-mini`
trên CÙNG bộ 5 kịch bản mẫu, cùng codebase**: đây là phép so sánh có giá
trị nhất trong tài liệu này vì kiểm soát được mọi biến khác (cùng tool,
cùng prompt, cùng dữ liệu) — chỉ đổi model.

| Khía cạnh | `gpt-oss-20b` (Cloudflare) | `gpt-4o-mini` (OpenAI) |
|---|---|---|
| Trigger đúng `tool_calls` chuẩn | 5/5 (test lặp lại, mục 1.2) | Ổn định qua toàn bộ 5 kịch bản, không quan sát thấy lỗi format |
| Chọn ĐÚNG tool tổng hợp (`compare_journeys`) khi so sánh nhiều tàu | Không có dữ liệu so sánh trực tiếp (tool này thêm sau) | **Không nhất quán giữa các lần chạy** — có lần gọi đúng `compare_journeys`, có lần tự gọi `get_journey` 29 lần rồi tự so sánh bằng tay, có lần dùng `list_vessels_by_type` dù được hướng dẫn rõ dùng `compare_journeys` |
| Độ chính xác khi tự tổng hợp thủ công nhiều kết quả | Không quan sát được (không rơi vào tình huống này) | **Phát hiện thật, nghiêm trọng**: 1 lần chạy tự gộp 29 kết quả `get_journey` rồi gán NHẦM số liệu của tàu này cho tên tàu khác (EVER GLOBE's 1074.66 hải lý bị gán cho "EVER GIFTED") — số liệu thật, tên sai. Lần chạy lặp lại sau đó lại ra đúng |
| Follow-up bằng đại từ trỏ đúng đối tượng đã pin (R3) | Không test (cơ chế pin fact thêm sau khi đã chuyển model) | **Phát hiện thật**: trả lời ĐÚNG bằng lời "đang theo dõi tàu MSC MANYA" (lượt 12), nhưng lượt kế tiếp gọi tool với `vessel_id` của tàu KHÁC (tàu vừa được hỏi ở lượt 11) — nhắc đúng nhưng hành động sai |
| Chi phí thực tế cho 1 lần chạy đủ 5 kịch bản (~20 lượt) | Miễn phí trong hạn ngạch Cloudflare (khi còn quota) | Dưới $0.05 (ước tính từ token usage thực tế, model rẻ) |

**Kết luận trung thực**: `gpt-4o-mini` vẫn đủ năng lực trigger tool-calling
đúng chuẩn ổn định hơn cả `qwen3.5-9b` lẫn ngang bằng `gpt-oss-20b` ở tầng
"gọi đúng cơ chế API", nhưng **suy luận đa bước và bám instruction ở tầng
"chọn đúng chiến lược/tool tối ưu" và "tổng hợp chính xác nhiều kết quả"
kém ổn định hơn** — đúng như dự đoán khi so sánh 2 tier model (mini vs
model đầy đủ/model chuyên biệt agentic như gpt-oss). Cả 2 bug thật tìm
được (gán nhầm tên tàu, nhầm vessel_id khi hành động) đều **không phải lỗi
định dạng/API** mà là lỗi suy luận thuần — không có cách "sửa dứt điểm"
bằng code, chỉ có thể giảm xác suất qua: (1) tool thiết kế tốt hơn (đã làm:
`compare_journeys` loại bỏ hẳn nhu cầu tự tổng hợp thủ công), (2) system
prompt nhắc thêm quy tắc cụ thể đúng loại lỗi đã gặp (đã làm — xem quy tắc
6/9 trong `src/prompts/system_prompts.py`), và/hoặc (3) **dùng model có
suy luận mạnh hơn** (`gpt-4.1`, `gpt-4o` đầy đủ, hoặc Claude Sonnet) nếu
độ chính xác quan trọng hơn chi phí — chi tiết đánh đổi xem mục 9.

## 2. Embedding

### 2.1. Các ứng viên đã cân nhắc

| Model | Đa ngôn ngữ? | Chiều | Ghi chú |
|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | Có, nhưng tối ưu chính cho tiếng Anh | 1536 | Lựa chọn mặc định ban đầu trong `.env.example` (giữ để tương thích khi dùng OpenAI thật) — yêu cầu tài khoản OpenAI riêng với LLM đang test |
| `bge-base-en-v1.5` | Không (thuần tiếng Anh) | 768 | Loại ngay — nội dung tóm tắt hội thoại gốc có thể lẫn tiếng Việt |
| `multilingual-e5-large` | Có | 1024 | Cân nhắc trên giấy, không test — không có sẵn qua cùng provider (Cloudflare) đang dùng cho LLM, thêm 1 provider = thêm 1 API key/1 điểm lỗi |
| Cohere `embed-multilingual-v3` | Có | 1024 | Cân nhắc trên giấy — chất lượng đa ngôn ngữ tốt theo tài liệu công khai, nhưng thêm nhà cung cấp thứ 3 không cần thiết ở quy mô bài test |
| **`@cf/baai/bge-m3`** (Cloudflare) | **Có, hỗ trợ tiếng Việt** | **1024** | **Đã chọn** |

**Lý do chọn `bge-m3` (ban đầu)**: đa ngôn ngữ thật (không chỉ tiếng Anh +
dịch máy), cùng provider với LLM đang dùng (1 API key, 1 hoá đơn, không thêm
điểm lỗi hạ tầng) — đúng nguyên tắc "ít moving part" đặt ra ở mục 0.

**Cập nhật sau khi đổi LLM sang OpenAI (mục 1.4)**: chuyển embedding sang
`text-embedding-3-small` (OpenAI thật) để cùng 1 provider với LLM (giữ
nguyên nguyên tắc "ít moving part"). Vấn đề kỹ thuật cần xử lý: model này
mặc định 1536 chiều, trong khi cột `memory_chunks.embedding` trong
`db/schema.sql` đã định nghĩa `vector(1024)` (khớp `bge-m3`) — đổi model
khác số chiều thường buộc phải migrate schema. Giải pháp: OpenAI
`text-embedding-3-*` hỗ trợ tham số `dimensions` (kỹ thuật Matryoshka
Representation Learning — huấn luyện sao cho các chiều đầu mang nhiều
thông tin nhất, cho phép cắt bớt chiều sau mà không cần huấn luyện lại)
— truyền `dimensions=1024` giữ nguyên schema cũ, không cần migrate DB. Đã
thêm biến môi trường `EMBEDDING_DIMENSIONS` (`src/utils/config.py`,
`src/models/embeddings.py`) chỉ truyền tham số này khi được cấu hình, để
không phá vỡ tương thích với provider không hỗ trợ nó (Cloudflare).

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

### 4.3. Cập nhật sau khi đổi sang OpenAI: tạm tắt rerank

**Giới hạn thật của OpenAI**: khác với Cloudflare Workers AI (LLM +
embedding + rerank trong cùng 1 nền tảng), **OpenAI không có sản phẩm
rerank** — API chỉ gồm chat completions, embeddings, và vài sản phẩm
chuyên biệt khác (audio, image...), không có endpoint cross-encoder rerank
nào. Vì Cloudflare cũng đang hết hạn ngạch miễn phí cùng lúc (mục 1.4),
không thể tiếp tục dùng `bge-reranker-base` như cũ mà không tạo thêm 1 tài
khoản/nhà cung cấp thứ 3 chỉ để có rerank (đi ngược nguyên tắc "ít moving
part" — mục 0).

**Quyết định**: tạm đặt `RERANKER_ENABLED=false`, chấp nhận quay lại dùng
thuần embedding similarity (thứ hạng, không ngưỡng tuyệt đối — mục 2.2) cho
nhánh truy xuất ngữ nghĩa. Rủi ro đã biết (bug #3 ở mục 6.2 — embedding một
mình không đủ phân biệt khi nhiều chunk cạnh tranh) **được bù đắp phần lớn**
bởi cơ chế pin fact tường minh bổ sung sau đó (mục 6.3) — vốn giải quyết
đúng use case quan trọng nhất (câu "ghi nhớ giúp tôi...") mà không cần
rerank. Nếu cần khôi phục rerank mà không thêm nhà cung cấp mới: Cohere có
gói miễn phí giới hạn cho Rerank API, hoặc tự host cross-encoder nhỏ
(`ms-marco-MiniLM`) — xem đánh đổi self-host ở mục 9.

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

### 6.4. Phát hiện thật với `gpt-4o-mini`: pin fact giải quyết "nhắc lại bằng lời", chưa giải quyết "hành động sau đó"

Sau khi đổi sang `gpt-4o-mini` (mục 1.4) và chạy lại Kịch bản 3, quan sát
được 1 biến thể MỚI của đúng lỗi "nhầm tàu vừa nhắc gần nhất" mà cơ chế pin
fact (6.3) chưa bao phủ hết:

- **Lượt 12** ("Hồ sơ tôi nhắc từ đầu... đang theo dõi tàu nào?"): trả lời
  ĐÚNG bằng lời — *"đang theo dõi tàu MSC MANYA"* — cơ chế pin fact hoạt
  động chính xác, PASS.
- **Lượt 13** ("Vị trí cuối cùng... của tàu đó"): gọi ĐÚNG tool
  (`get_position_at_time`, không kèm `at_ts` — dùng đúng cơ chế "vị trí mới
  nhất" mới thêm, xem `docs/architecture.md` mục 7), nhưng truyền
  `vessel_id` của **TENGXIANHAIXIANG77** — tàu được hỏi ở lượt 11, tàu GẦN
  NHẤT về mặt thứ tự lời gọi tool — thay vì `vessel_id` của MSC MANYA, tàu
  vừa được chính nó xác nhận đúng ở lượt 12 ngay trước. FAIL.

**Phân tích**: pin fact (6.3) đảm bảo *thông tin* MSC MANYA luôn có mặt
trong context (giải quyết được việc NHẮC LẠI BẰNG LỜI ở lượt 12), nhưng
không có cơ chế nào buộc bước HÀNH ĐỘNG (chọn `vessel_id` để gọi tool) ở
lượt kế tiếp phải dùng đúng thực thể vừa nhắc — model dường như ưu tiên
"tàu gần nhất trong lịch sử tool-calling" hơn "tàu vừa nêu tên trong chính
câu trả lời của nó". Đây là lỗi suy luận/liên kết ngữ cảnh, không phải lỗi
truy xuất bộ nhớ — **nằm ngoài phạm vi mà pin fact có thể sửa**, vì pin
fact chỉ đảm bảo dữ liệu có mặt, không đảm bảo model dùng đúng dữ liệu đó
khi hành động.

**Hướng xử lý đã áp dụng**: thêm 1 quy tắc cụ thể vào `SYSTEM_PROMPT` (quy
tắc 6, `src/prompts/system_prompts.py`) yêu cầu model tự đối chiếu
`vessel_id` truyền vào tool với tên tàu vừa nêu trong câu trả lời liền
trước — đây là biện pháp giảm xác suất (prompt-level), không phải sửa dứt
điểm, nhất quán với kết luận chung của toàn mục 6: **cơ chế nào cũng có
trần độ tin cậy phụ thuộc vào năng lực suy luận của model đang dùng** — mô
hình nhỏ/rẻ hơn (dù tool-calling format ổn định) vẫn có thể mắc lỗi liên
kết ngữ cảnh mà mô hình có suy luận mạnh hơn ít gặp hơn. Xem mục 9 để biết
đánh đổi khi cần độ tin cậy cao hơn.

## 7. Framework backend

**FastAPI + PostgreSQL/PostGIS + Docker Compose** — theo đúng gợi ý của đề
bài. Vài điểm cân nhắc thêm không có trong gợi ý gốc:

| Quyết định | Lý do |
|---|---|
| SSE (`StreamingResponse`) thay vì WebSocket | Giao tiếp chat ở đây về bản chất **1 chiều theo lượt** (client gửi 1 message, server trả về 1 luồng sự kiện rồi đóng) — không cần kênh 2 chiều liên tục của WebSocket. SSE đơn giản hơn (không cần quản lý handshake/ping-pong riêng), FastAPI hỗ trợ tốt qua `StreamingResponse`, và debug được bằng `curl -N` thuần (yêu cầu D1) mà không cần client WebSocket riêng |
| PostgreSQL + PostGIS thay vì MongoDB/Elasticsearch cho dữ liệu không gian | PostGIS là lựa chọn tiêu chuẩn ngành cho dữ liệu địa lý quan hệ (index GiST, hàm `ST_*` phong phú, hỗ trợ `geography` cho tính khoảng cách chính xác trên mặt cầu) — MongoDB geo-index đơn giản hơn nhưng thiếu các phép tính hình học phức tạp (`ST_Simplify`, `ST_MakeLine` có `ORDER BY`) mà N2/N3 cần |
| 1 database cho cả dữ liệu tàu biển + hội thoại + vector | Xem mục 3 — giảm số lượng service cần vận hành trong 7 ngày |

## 8. Bảng tổng hợp lựa chọn cuối

**Đã đổi sau 1 vòng review** (lý do đầy đủ: mục 1.4) — bảng dưới đây phản
ánh trạng thái ĐANG DÙNG, không phải lựa chọn ban đầu (`gpt-oss-20b` +
`bge-m3` + `bge-reranker-base` qua Cloudflare) — quá trình/lý do ban đầu
vẫn giữ nguyên ở các mục trên vì đó là bằng chứng thật quan trọng, không
xoá lịch sử quyết định.

| Thành phần | Lựa chọn hiện tại | Lựa chọn ban đầu | Lý do đổi (1 dòng) |
|---|---|---|---|
| LLM | `gpt-4o-mini` (OpenAI thật) | `gpt-oss-20b` (Cloudflare) | Cloudflare hết hạn ngạch miễn phí giữa lúc test; OpenAI thật = zero thay đổi code (mục 1.4) |
| Embedding | `text-embedding-3-small`, `dimensions=1024` (OpenAI) | `bge-m3` (Cloudflare) | Cùng provider với LLM mới; giữ nguyên schema `vector(1024)` nhờ tham số `dimensions` |
| Vector DB | pgvector (không đổi) | pgvector | Không thêm service, đủ nhanh ở quy mô bài test |
| Reranker | Tắt (`RERANKER_ENABLED=false`) | `bge-reranker-base` (Cloudflare) | OpenAI không có sản phẩm rerank; bù bằng cơ chế pin fact (mục 4.3, 6.3) |
| Chiến lược bộ nhớ | Kết hợp + pin fact tường minh (không đổi) | — | Phương án đạt tỷ lệ pass cao nhất khi kiểm chứng bằng LLM thật |
| Framework agent | Tự viết (~135 dòng, không đổi) | — | Bám sát yêu cầu "phải giải thích được mọi phần" |
| Backend | FastAPI + SSE + PostgreSQL/PostGIS + Docker Compose (không đổi) | — | Đúng gợi ý đề bài, SSE đủ cho giao tiếp 1 chiều theo lượt |

## 9. Nếu có hạ tầng riêng: hướng self-host thay vì dùng API

Toàn bộ lựa chọn LLM/embedding/rerank ở trên đều là **managed API** (trả
tiền theo token, không quản lý hạ tầng). Đây là lựa chọn hợp lý cho 1 bài
test 7 ngày làm một mình, nhưng **nếu có hạ tầng riêng (GPU server) và bài
toán chạy dài hạn ở quy mô lớn hơn**, hướng self-host (tự triển khai model
mở qua vLLM/TGI/Ollama trên GPU riêng) đáng cân nhắc nghiêm túc — dưới đây
là các điểm mạnh cụ thể, đối chiếu với đúng những vấn đề thật đã gặp trong
quá trình làm bài test này (không phải lý thuyết suông):

| Điểm mạnh của self-host | Đối chiếu với vấn đề thật đã gặp |
|---|---|
| **Không giới hạn hạn ngạch/rate limit** | Chính là sự cố dẫn đến phải đổi provider giữa chừng (mục 1.4) — Cloudflare hết 10.000 neurons/ngày ở gói miễn phí. Self-host trên GPU riêng không có khái niệm "hạn ngạch ngày" — chỉ giới hạn bởi throughput phần cứng của chính mình |
| **Chi phí biên = 0 sau đầu tư ban đầu** | Ở quy mô bài test, chi phí API không đáng kể (mục 8.2 `docs/architecture.md`) — nhưng ở quy mô production thật (hàng chục nghìn lượt/ngày), chi phí API cộng dồn tuyến tính theo token, trong khi GPU tự có chi phí cố định (khấu hao/điện) không đổi theo lượng dùng — hoà vốn nhanh ở tải cao |
| **Không phụ thuộc uptime của bên thứ 3** | Lỗi 500 kéo dài của Cloudflare ở Kịch bản 5 (mục 1.3) là ví dụ thật — self-host loại bỏ hoàn toàn phụ thuộc vào SLA của nhà cung cấp ngoài (dù đổi lại là tự chịu trách nhiệm vận hành uptime của chính mình) |
| **Kiểm soát dữ liệu/quyền riêng tư** | Dữ liệu AIS/đăng kiểm/chủ sở hữu tàu trong bài toán này không đặc biệt nhạy cảm, nhưng ở ứng dụng thật (vd. dữ liệu vận hành của 1 hãng tàu), việc dữ liệu không rời khỏi hạ tầng riêng (không gửi qua API bên thứ 3) có thể là yêu cầu bắt buộc về compliance |
| **Tự do chọn tool-call parser/định dạng phù hợp nhất** | Vấn đề gốc khiến `qwen3.5-9b` fail (mục 1.2) là do server vLLM tự host THIẾU cấu hình `--tool-call-parser` — đây là **nhược điểm** của self-host (phải tự cấu hình đúng), nhưng đồng thời cũng là **điểm mạnh**: khi cấu hình đúng, có toàn quyền chọn/đổi model, không bị khoá vào 1 định dạng/nhà cung cấp |
| **Có thể tự host reranker mà không phụ thuộc "danh mục sản phẩm" của nhà cung cấp** | Đúng vấn đề vừa gặp ở mục 4.3 — OpenAI không có sản phẩm rerank, phải tắt hoặc tìm nhà cung cấp thứ 3. Self-host cross-encoder (`bge-reranker-base`, `ms-marco-MiniLM`...) chạy trực tiếp trên GPU riêng, không phụ thuộc việc 1 API có "bán" tính năng đó hay không |
| **Tinh chỉnh/fine-tune được cho đúng domain** | Không cần thiết ở quy mô bài test, nhưng nếu dữ liệu tàu biển mở rộng lâu dài, có thể fine-tune model mở cho đúng thuật ngữ hàng hải/định dạng trả lời mong muốn — không thể làm điều này với model đóng qua API |
| **Độ trễ có thể dự đoán/kiểm soát được** | Managed API cộng thêm độ trễ mạng + hàng đợi phía nhà cung cấp (biến thiên, ngoài tầm kiểm soát); self-host trên phần cứng riêng, cùng mạng nội bộ, cho độ trễ ổn định hơn — quan trọng nếu cần SLA chặt cho ứng dụng thời gian thực |

**Đánh đổi cần nêu trung thực (không chỉ nêu điểm mạnh)**: self-host đổi
lấy toàn bộ trách nhiệm vận hành (uptime, bảo mật, nâng cấp, giám sát GPU)
từ nhà cung cấp sang chính đội ngũ của mình, và **chính sự cố thật đã gặp
với `qwen3.5-9b`** (thiếu 1 dòng cấu hình `--tool-call-parser` khiến toàn
bộ tool-calling fail âm thầm — mục 1.2) là ví dụ cụ thể cho thấy self-host
đòi hỏi năng lực vận hành hạ tầng inference đúng đắn, không chỉ đơn giản
là "chạy model lên GPU". Với 1 bài test 7 ngày làm một mình không có GPU
server sẵn, managed API vẫn là lựa chọn đúng — hướng self-host chỉ nên cân
nhắc khi đã có hạ tầng và đội ngũ vận hành phù hợp, đúng như tiêu đề mục
này đặt ra ("nếu có hạ tầng riêng").
