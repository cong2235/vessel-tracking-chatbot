# Nghiên cứu và lựa chọn công nghệ

## 1. LLM

**Đã thử 2 lựa chọn thực tế, không chỉ lý thuyết:**

| Model | Kết quả thử nghiệm thật |
|---|---|
| `qwen3.5-9b` (self-hosted qua vLLM, endpoint nội bộ) | **Không ổn định** — 0/5 lần lặp lại cùng 1 câu hỏi (nhiệt độ 0) trigger đúng cơ chế `tool_calls` chuẩn của API; model in tool-call dưới dạng text thô (`<tool_call> search_vessel(...)`), nghi do server vLLM thiếu cấu hình `--tool-call-parser hermes` cho Qwen. Khi lỗi này xảy ra, toàn bộ câu trả lời sau đó bị bịa — vi phạm trực tiếp R4. |
| `@cf/openai/gpt-oss-20b` (Cloudflare Workers AI) | **Ổn định** — 5/5 lần lặp lại trigger đúng tool_calls. Chạy đầy đủ 5 kịch bản mẫu trong đề bài, đối chiếu dữ liệu thật, đạt tủ lệ đúng cao (xem `results/`). |

**Lý do chọn `gpt-oss-20b`:**
- Là model do chính OpenAI phát hành dạng open-weight, được thiết kế riêng
  cho agentic tool-calling (định dạng Harmony có channel suy luận riêng).
- Giá rẻ ($0.2/$0.3 mỗi triệu token input/output), context 128K.
- Có sẵn qua Cloudflare Workers AI — không cần tự host, không cần lo hạ
  tầng GPU, và API tương thích chuẩn OpenAI Chat Completions nên không
  cần viết code riêng cho provider này.

**Quirk phát hiện khi test thật (không phải giả định):**
- Dùng `reasoning_content` (chain-of-thought riêng) trước khi ra `content`
  cuối — nếu `max_tokens` quá nhỏ, model dùng hết ngân sách token vào suy
  luận, `content` trả về rỗng dù `finish_reason="length"` (đã tăng
  `LLM_MAX_TOKENS` từ 1024 → 4096 sau khi phát hiện qua test câu hỏi phức
  tạp N3 nhiều bước).
- Một API OpenAI-compatible như Cloudflare có thể **khác chuẩn OpenAI thật**
  ở các chi tiết nhỏ — vd. từ chối `content: null` cho message có
  `tool_calls` (chuẩn OpenAI cho phép), phải đổi sang `content: ""`.
- Occasionally rò rỉ token định dạng nội bộ vào tên tool (vd.
  `get_vessel_info<|channel|>analysis`) — tool không tồn tại được xử lý
  graceful (trả lỗi cho model, không crash), model tự gọi lại đúng tên ở
  lượt sau.

## 2. Embedding

**`@cf/baai/bge-m3`** (Cloudflare Workers AI), 1024 chiều.

Lý do: đa ngôn ngữ (hỗ trợ tiếng Việt), trong khi
`text-embedding-3-small` (OpenAI, lựa chọn mặc định ban đầu) yêu cầu tài
khoản OpenAI riêng, và các model embedding tiếng Anh thuần
(`bge-base-en-v1.5`) không phù hợp với nội dung tiếng Việt.

**Phát hiện quan trọng qua test thật**: dù đa ngôn ngữ, điểm cosine
similarity mà `bge-m3` cho ra trên các bản tóm tắt hội thoại NGẮN (dưới
150 từ) rất thấp và hẹp (0.24–0.35 trên thang 0–1), kể cả giữa câu hỏi và
đoạn văn liên quan nhất. Điều này khiến ngưỡng similarity cố định (ban đầu
đặt 0.5 theo trực giác kiểu OpenAI) **lọc mất cả kết quả đúng nhất** — phải
hạ xuống 0.15 và chuyển sang dựa vào thứ tự xếp hạng (`ORDER BY` + `LIMIT`)
thay vì ngưỡng tuyệt đối.

## 3. Vector database

**pgvector** (extension của chính PostgreSQL đang dùng), không dùng
Qdrant/Milvus/Chroma riêng.

Lý do: dữ liệu tàu biển (R1) đã cần PostGIS trên Postgres; dùng luôn
pgvector trên CÙNG database giảm hẳn độ phức tạp hạ tầng (không cần thêm
service, thêm kết nối, thêm cơ chế đồng bộ) — hợp lý cho quy mô bài test
(vài trăm–vài nghìn chunk mỗi hội thoại). Nếu quy mô lớn hơn nhiều (hàng
triệu vector, nhiều tenant), Qdrant/Milvus sẽ có lợi thế về hiệu năng
index chuyên biệt (HNSW tối ưu hơn, sharding sẵn) — ghi vào hướng mở rộng.

## 4. Reranker

**`@cf/baai/bge-reranker-base`** (Cloudflare Workers AI) — thêm sau khi
phát hiện embedding một mình không đủ phân biệt khi có nhiều chunk cạnh
tranh (xem mục "So sánh chiến lược bộ nhớ" ở `docs/architecture.md` mục 3,
và chi tiết root-cause bên dưới).

**Phát hiện quan trọng qua test thật**: `bge-reranker-base` (cross-encoder)
hoạt động RẤT tốt để phân biệt văn bản liên quan/không liên quan (0.62 vs
0.0001-0.0003 trên thang xác suất) — nhưng **chỉ với tiếng Anh**. Test cùng
1 tình huống bằng tiếng Việt cho kết quả gần như ngẫu nhiên (context đúng
xếp HẠNG THẤP NHẤT trong 3 lựa chọn). Đây là lý do quyết định đổi
`SUMMARIZE_PROMPT` sang yêu cầu tóm tắt bằng **tiếng Anh** — vì
`memory_chunks` chỉ là dữ liệu nội bộ cho LLM đọc (không hiển thị trực
tiếp cho người dùng), đổi ngôn ngữ tóm tắt không ảnh hưởng trải nghiệm
(câu trả lời cuối luôn bằng tiếng Việt theo system prompt).

## 5. Framework agent

**Không dùng LangChain/LlamaIndex/LangGraph.** Tự viết vòng lặp
tool-calling (`src/agent/agent.py`, ~120 dòng cho cả bản thường và bản
streaming).

Lý do: đề bài yêu cầu "phải giải thích được mọi phần trong tài liệu mô
tả" — một vòng lặp tự viết (gọi LLM → có tool_call thì chạy tool → đưa kết
quả lại → lặp) đơn giản, tường minh, dễ debug hơn nhiều so với việc phải
giải thích các lớp trừu tượng bên trong 1 framework agent nặng. Với 8 tool
và luồng tuyến tính, lợi ích của framework (orchestration phức tạp, đa
agent, graph có nhánh...) không cần thiết.

## 6. So sánh 4 chiến lược bộ nhớ dài hạn

Xem bảng so sánh chi tiết tại `docs/architecture.md` mục 3. Tóm tắt lựa
chọn: **kết hợp cả 4** — cửa sổ trượt (giữ nguyên văn gần đây) + tóm tắt
(nén phần cũ) + embedding retrieval (tìm theo ngữ nghĩa) + rerank (tăng độ
chính xác retrieval). Đây là lựa chọn phức tạp nhất trong 4 phương án,
nhưng là lựa chọn DUY NHẤT đáp ứng được yêu cầu Kịch bản 3 của đề bài (nhớ
đúng thông tin từ lượt 1 sau ≥10 lượt) khi kiểm chứng bằng LLM thật — thử
nghiệm với các phiên bản đơn giản hơn (chỉ threshold similarity, không
rerank) đã THẤT BẠI thật khi test (xem `results/` và lịch sử phát triển).

## 7. Framework backend

**FastAPI + PostgreSQL/PostGIS + Docker Compose** — theo đúng gợi ý của đề
bài, không có lý do để lệch khỏi gợi ý này (FastAPI hỗ trợ SSE tốt qua
`StreamingResponse`, PostGIS là lựa chọn tiêu chuẩn cho dữ liệu không
gian).
