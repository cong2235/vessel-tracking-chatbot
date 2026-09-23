# Nghiên cứu và lựa chọn công nghệ

## 0. Phương pháp và tiêu chí đánh giá

Tài liệu này trình bày quá trình dẫn đến lựa chọn cuối cùng, không chỉ nêu
kết quả — bao gồm các phương án đã được cân nhắc nhưng không lựa chọn, các
phương án đã được kiểm thử trực tiếp và không đạt yêu cầu, cùng nguyên nhân
gốc của từng trường hợp không đạt. Nguyên tắc trình bày xuyên suốt: một kết
luận chỉ được ghi nhận là "đã kiểm chứng" khi có bằng chứng cụ thể (nhật ký
hệ thống, transcript, số liệu đo được); phần nào chỉ dựa trên tài liệu công
khai của nhà cung cấp mà chưa được kiểm thử trực tiếp sẽ được ghi chú rõ là
"cân nhắc trên cơ sở lý thuyết".

Tiêu chí đánh giá áp dụng chung cho mọi lựa chọn, xếp theo mức độ ưu tiên
dành riêng cho phạm vi bài toán này:

| Tiêu chí | Mức độ liên quan |
|---|---|
| **Độ tin cậy của tool-calling** | Yêu cầu R4 đòi hỏi hệ thống không được tự suy diễn dữ liệu — nếu model không kích hoạt đúng cơ chế `tool_calls` chuẩn, toàn bộ pipeline mất tác dụng và model sẽ tự tổng hợp câu trả lời không dựa trên dữ liệu thật |
| **Hỗ trợ tiếng Việt** | Người dùng đặt câu hỏi bằng tiếng Việt trong khi dữ liệu gốc (nhãn loại tàu) ở dạng tiếng Anh — model và embedding cần xử lý tốt cả hai ngôn ngữ |
| **Chi phí ở quy mô triển khai thử nghiệm** | Khối lượng truy vấn phục vụ đánh giá ở mức vài trăm lượt, tương ứng ngân sách cá nhân |
| **Độ phức tạp hạ tầng** | Thời hạn triển khai 7 ngày, thực hiện độc lập — ưu tiên giải pháp có ít thành phần vận hành |
| **Khả năng diễn giải được** | Yêu cầu của đề bài quy định mọi phần trong tài liệu mô tả phải được giải thích được, kể cả khi có sử dụng framework hoặc công cụ hỗ trợ |

## 1. LLM

### 1.1. Các ứng viên đã cân nhắc

| Model | Loại | Đánh giá sơ bộ | Lý do không lựa chọn / không kiểm thử |
|---|---|---|---|
| GPT-4o-mini / GPT-4.1-mini (OpenAI) | API trả phí | Tool-calling ổn định, context 128K, chi phí thấp trong nhóm managed API | Chưa kiểm thử trực tiếp ở giai đoạn đầu — ưu tiên kiểm thử một model open-weight trước để đối chiếu chi phí và độ ổn định thực tế trước khi cam kết dùng provider đóng |
| Claude Haiku (Anthropic) | API trả phí | Tool-calling tốt, bám sát instruction — phù hợp yêu cầu nghiêm ngặt về việc không suy diễn dữ liệu của R4 | Không có tài khoản sẵn sàng trong thời gian triển khai; giữ lại làm hướng mở rộng |
| Gemini Flash (Google) | API trả phí | Chi phí thấp, context dài | Cấu trúc function-calling schema khác biệt so với chuẩn OpenAI, có rủi ro phát sinh thời gian debug định dạng thay vì debug logic nghiệp vụ |
| Qwen2.5/3.5 (self-host qua vLLM) | Model mở | Miễn phí (chỉ phát sinh chi phí hạ tầng tự vận hành), hỗ trợ tiếng Việt tương đối tốt | Đã kiểm thử trực tiếp — xem mục 1.2; không đạt do nguyên nhân hạ tầng inference, không phải do năng lực model |
| Llama 3.1/3.3 (self-host) | Model mở | Cộng đồng lớn, nhiều công cụ hỗ trợ | Không kiểm thử — cùng nhóm rủi ro hạ tầng tự host như Qwen; ưu tiên thời gian cho hướng managed-inference của model mở (Cloudflare Workers AI) |
| `gpt-oss-20b`/`gpt-oss-120b` (OpenAI, open-weight) | Model mở, qua managed inference | Thiết kế chuyên biệt cho agentic tool-calling (định dạng Harmony có kênh suy luận riêng), context 128K | Đã kiểm thử trực tiếp — xem mục 1.2; lựa chọn ban đầu |
| DeepSeek-V3 | Model mở | Chi phí thấp, kết quả benchmark công khai tốt | Không có sẵn qua managed-inference provider đang sử dụng (Cloudflare) tại thời điểm triển khai; không đủ thời gian dựng thêm hạ tầng inference riêng |

**Kết luận thu hẹp phạm vi**: giữa nhóm managed-API trả phí (OpenAI/
Anthropic/Gemini — độ ổn định cao nhưng chưa được kiểm chứng trực tiếp) và
nhóm model mở tự host/managed-inference (chi phí thấp hơn nhưng độ tin cậy
tool-calling chưa rõ ràng), quyết định được đưa ra là kiểm thử trực tiếp hai
phương án ở nhóm chi phí thấp nhất (self-host Qwen và managed gpt-oss) để có
dữ liệu thực nghiệm về độ ổn định, thay vì mặc định lựa chọn OpenAI theo
thông lệ phổ biến — phù hợp với yêu cầu của đề bài rằng mọi lựa chọn phải có
căn cứ giải thích được.

### 1.2. Kiểm thử thực nghiệm: `qwen3.5-9b` (self-host) so với `gpt-oss-20b` (Cloudflare)

**Phương pháp**: sử dụng cùng một câu hỏi cố định — *"Cho tôi thông tin về
tàu KOTA GAYA"* (kích hoạt đúng một lời gọi tool `search_vessel`) — lặp lại
5 lần độc lập ở `temperature=0` cho mỗi model, qua cùng một đường code
(`src/agent/agent.py::run_agent_turn`, không thay đổi gì giữa hai lần kiểm
thử ngoài `OPENAI_BASE_URL`/`OPENAI_CHAT_MODEL`). Tiêu chí đạt: model trả về
đúng trường `tool_calls` theo chuẩn OpenAI Chat Completions API, không phải
văn bản mô phỏng lời gọi hàm.

| Model | Hạ tầng | Kết quả (5 lần lặp) | Ghi chú |
|---|---|---|---|
| `qwen3.5-9b` | Self-host qua vLLM, endpoint nội bộ | 0/5 | Model xuất lời gọi tool dưới dạng văn bản thô `<tool_call> search_vessel(...)` thay vì trường `tool_calls` |
| `@cf/openai/gpt-oss-20b` | Cloudflare Workers AI (managed) | 5/5 | Kích hoạt đúng `tool_calls` ở mọi lần lặp, câu trả lời khớp hoàn toàn với dữ liệu thực tế (đối chiếu thủ công) |

**Phân tích nguyên nhân đối với `qwen3.5-9b`**: nguyên nhân có khả năng cao
nhất là server vLLM thiếu cấu hình `--tool-call-parser hermes` (Qwen sử dụng
định dạng function-call riêng trong chat template, vLLM cần parser tương ứng
để bóc tách thành `tool_calls` chuẩn OpenAI; nếu thiếu, toàn bộ nội dung rơi
vào trường `content` dưới dạng văn bản). Đây là lỗi cấu hình hạ tầng
inference tự host, không phải lỗi năng lực model hay lỗi trong vòng lặp
tool-calling của hệ thống (vòng lặp đã được kiểm thử riêng bằng mock, xem
`README.md` mục 5). Hệ quả khi lỗi này xảy ra: theo đúng thiết kế, hệ thống
coi trường `content` trả về là câu trả lời cuối cùng — không tool nào được
thực thi — model tự tổng hợp phần còn lại từ kiến thức chung, vi phạm trực
tiếp yêu cầu R4. Đây là căn cứ cho quyết định không tiếp tục khắc phục hạ
tầng vLLM trong phạm vi 7 ngày mà chuyển sang managed inference.

**Căn cứ lựa chọn `gpt-oss-20b` (ngoài kết quả kiểm thử):**
- Model do OpenAI phát hành dưới dạng open-weight, thiết kế chuyên biệt cho
  agentic tool-calling (định dạng Harmony có kênh suy luận riêng).
- Chi phí thấp ($0,2 / $0,3 trên mỗi triệu token input/output theo bảng giá
  Cloudflare Workers AI tại thời điểm biên soạn tài liệu), context 128K.
- Có sẵn qua Cloudflare Workers AI, không cần tự host hay quản lý hạ tầng
  GPU; API tương thích chuẩn OpenAI Chat Completions nên không phát sinh
  code riêng cho provider này (chỉ cần thay đổi ba biến môi trường).

### 1.3. Các đặc điểm phát hiện qua kiểm thử thực nghiệm

| # | Vấn đề | Triệu chứng | Nguyên nhân | Biện pháp khắc phục | File |
|---|---|---|---|---|---|
| 1 | `max_tokens` mặc định quá nhỏ | `content` rỗng dù `finish_reason="length"` | `gpt-oss` sử dụng `reasoning_content` (chuỗi suy luận riêng theo định dạng Harmony) tiêu tốn hết ngân sách token trước khi sinh `content` cuối | Bổ sung biến môi trường `LLM_MAX_TOKENS`, nâng giá trị mặc định từ 1024 lên 4096 sau khi kiểm thử với câu hỏi N3 nhiều bước | `src/utils/config.py::get_max_tokens` |
| 2 | `content: null` bị từ chối (HTTP 400) | Request lỗi khi message `assistant` có `tool_calls` | Chuẩn OpenAI cho phép `content: null` với message có `tool_calls`, nhưng Cloudflare kiểm tra chặt hơn và yêu cầu kiểu string | Đổi sang `content: ""` — vẫn tương thích ngược với OpenAI gốc | `src/models/llm_client.py` |
| 3 | Token định dạng nội bộ lẫn vào tên tool | Tool được gọi có tên dạng `get_vessel_info<|channel|>analysis` | Cơ chế phân tách kênh suy luận/nội dung của Harmony đôi khi lẫn vào output tên hàm | Không xử lý ở tầng model — tận dụng cơ chế sẵn có "tool không tồn tại trả lỗi cho model" (`agent.py::_execute_tool`); model tự phục hồi và gọi lại đúng tên ở lượt sau, phát sinh thêm một vòng lặp nhưng không gây crash | `src/agent/agent.py::_execute_tool` |
| 4 | Trùng lặp tham số trong một lời gọi tool | Model gọi `vessel_ids: [id1, id1]` thay vì một lần | Chưa xác định được nguyên nhân gốc (có thể liên quan đến decode lặp ở tầng streaming của provider) | Không cần xử lý — các câu lệnh SQL của tool đã dùng `GROUP BY`/`ANY()` nên trùng lặp không ảnh hưởng kết quả, chỉ phát sinh chi phí token thừa | — |
| 5 | Lỗi `500 Internal Server Error` không ổn định | Một lần chạy `scripts/run_scenarios.py` bị gián đoạn giữa chừng | Hạ tầng inference dùng chung/chi phí thấp của Cloudflare không đảm bảo uptime tuyệt đối cho mọi request | Bổ sung retry (`tenacity`, tối đa 3 lần, backoff tăng dần), chỉ áp dụng cho lỗi 5xx/mất kết nối, không retry lỗi 4xx | `src/models/llm_client.py::_create_completion` |

Ghi nhận bổ sung: trong một lần chạy khác (Kịch bản 5, lượt 2–3,
`results/scenario_5.md`), lỗi 500 kéo dài hơn cả ba lần retry (~10 giây) —
đây là rủi ro vận hành thực tế khi sử dụng hạ tầng inference dùng chung/chi
phí thấp, không phải lỗi trong code ứng dụng. Một hệ thống production cần bổ
sung cơ chế cảnh báo (alerting) và có thể cần phương án dự phòng sang
provider khác khi một provider gián đoạn kéo dài; nội dung này nằm ngoài
phạm vi triển khai 7 ngày (xem `docs/architecture.md`, mục "Hạn chế còn tồn
tại").

### 1.4. Chuyển sang `gpt-4o-mini` (OpenAI) sau khi phát sinh giới hạn hạ tầng

**Bối cảnh dẫn đến quyết định chuyển đổi**: trong quá trình chạy lại năm
kịch bản mẫu để kiểm chứng các bản sửa lỗi, tài khoản Cloudflare Workers AI
báo lỗi `429 — you have used up your daily free allocation of 10,000
neurons`. Đây đúng là rủi ro đã được ghi nhận ở mục 1.3 (hạ tầng inference
dùng chung/chi phí thấp không đảm bảo uptime), nhưng ở lần này gây gián đoạn
hoàn toàn việc kiểm thử thay vì chỉ làm chậm một request đơn lẻ. Quyết định
được đưa ra: tách riêng tiêu chí "lựa chọn theo hạ tầng sẵn có" khỏi "lựa
chọn theo chi phí và mức độ phù hợp thuần tuý" — khi bỏ qua yếu tố hạ tầng,
phương án hợp lý nhất là sử dụng trực tiếp OpenAI, do `src/models/
llm_client.py` vốn được viết đúng theo chuẩn OpenAI Chat Completions gốc
(không phải bản mô phỏng của Cloudflare) nên việc chuyển provider không đòi
hỏi thay đổi code ở phần gọi LLM.

**Sự cố phát sinh khi chuyển đổi (lỗi hạ tầng, không phải lỗi logic)**: dòng
cấu hình `OPENAI_BASE_URL=` (giá trị rỗng) trong `.env` — theo đúng hướng
dẫn trước đó của `.env.example` ("để trống nhằm sử dụng OpenAI mặc định") —
khiến OpenAI SDK báo lỗi `UnsupportedProtocol: Request URL is missing an
'http://' or 'https://' protocol`. Nguyên nhân: SDK đọc trực tiếp biến môi
trường `OPENAI_BASE_URL` từ `os.environ`, và một biến rỗng nhưng tồn tại có
hành vi khác với biến không tồn tại — `os.environ.get("OPENAI_BASE_URL",
DEFAULT)` trả về `""` (do key vẫn tồn tại) thay vì trả về `DEFAULT`. Việc
`src/utils/config.py::get_openai_base_url()` tự chuyển `"" -> None` không đủ
để khắc phục, vì SDK đọc thẳng biến môi trường ở tầng riêng của nó, không đi
qua hàm cấu hình này. Biện pháp khắc phục gồm hai lớp: xoá biến rỗng khỏi
`os.environ` trước khi khởi tạo client (`src/models/llm_client.py::
get_client`), đồng thời cập nhật hướng dẫn trong `.env.example` khuyến nghị
xoá hẳn dòng cấu hình thay vì để trống. Đã bổ sung một unit test hồi quy
(`tests/test_llm_client_retry.py::
test_get_client_ignores_empty_string_base_url_env_var`).

**Đối chiếu chất lượng suy luận giữa `gpt-oss-20b` và `gpt-4o-mini` trên
cùng bộ năm kịch bản mẫu, cùng codebase**: đây là phép so sánh có giá trị
tham chiếu cao nhất trong tài liệu này vì kiểm soát được mọi biến số khác
(cùng tool, cùng prompt, cùng dữ liệu), chỉ thay đổi model.

| Khía cạnh | `gpt-oss-20b` (Cloudflare) | `gpt-4o-mini` (OpenAI) |
|---|---|---|
| Kích hoạt đúng `tool_calls` chuẩn | 5/5 (kiểm thử lặp lại, mục 1.2) | Ổn định trên toàn bộ 5 kịch bản, không ghi nhận lỗi định dạng |
| Lựa chọn đúng tool tổng hợp (`compare_journeys`) khi so sánh nhiều tàu | Không có dữ liệu so sánh trực tiếp (tool này được bổ sung sau) | Không nhất quán giữa các lần chạy — có lần gọi đúng `compare_journeys`, có lần tự gọi `get_journey` 29 lần rồi tự tổng hợp thủ công, có lần dùng `list_vessels_by_type` dù được hướng dẫn rõ dùng `compare_journeys` |
| Độ chính xác khi tự tổng hợp thủ công nhiều kết quả | Không quan sát được (không rơi vào tình huống này) | Phát hiện đáng chú ý: một lần chạy tự gộp 29 kết quả `get_journey` rồi gán nhầm số liệu của một tàu cho tên tàu khác (số liệu 1074,66 hải lý của EVER GLOBE bị gán cho "EVER GIFTED") — số liệu đúng, tên sai. Lần chạy lặp lại sau đó cho kết quả đúng |
| Follow-up bằng đại từ trỏ đúng đối tượng đã pin (R3) | Không kiểm thử (cơ chế pin fact được bổ sung sau khi đã chuyển model) | Phát hiện đáng chú ý: trả lời đúng bằng lời — "đang theo dõi tàu MSC MANYA" (lượt 12) — nhưng lượt kế tiếp gọi tool với `vessel_id` của tàu khác (tàu vừa được hỏi ở lượt 11); nội dung trả lời đúng nhưng hành động sai |
| Chi phí cho một lần chạy đủ 5 kịch bản (~20 lượt) | Miễn phí trong hạn ngạch Cloudflare (khi còn quota) | Dưới $0,05 (ước tính từ số liệu token usage thực tế) |

**Kết luận**: `gpt-4o-mini` có độ tin cậy kích hoạt tool-calling đúng chuẩn
tương đương hoặc cao hơn `qwen3.5-9b` lẫn `gpt-oss-20b` ở tầng "gọi đúng cơ
chế API", nhưng khả năng suy luận đa bước và bám instruction ở tầng "lựa
chọn đúng chiến lược/tool tối ưu" và "tổng hợp chính xác nhiều kết quả" kém
ổn định hơn — phù hợp với kỳ vọng khi so sánh hai nhóm model (mini so với
model đầy đủ/model chuyên biệt cho tác vụ agentic như gpt-oss). Cả hai lỗi
thực nghiệm phát hiện được (gán nhầm tên tàu, nhầm vessel_id khi hành động)
đều không phải lỗi định dạng/API mà là lỗi suy luận thuần tuý — không có
biện pháp khắc phục dứt điểm bằng code, chỉ có thể giảm xác suất xảy ra
thông qua: (1) thiết kế tool tốt hơn (đã thực hiện: `compare_journeys` loại
bỏ hoàn toàn nhu cầu tự tổng hợp thủ công), (2) bổ sung quy tắc cụ thể vào
system prompt tương ứng với từng loại lỗi đã phát hiện (đã thực hiện — xem
quy tắc 6/9 trong `src/prompts/system_prompts.py`), và/hoặc (3) sử dụng
model có năng lực suy luận cao hơn (`gpt-4.1`, `gpt-4o` đầy đủ, hoặc Claude
Sonnet) khi độ chính xác được ưu tiên hơn chi phí — chi tiết đánh đổi xem
mục 9.

### 1.5. Hướng phát triển tiếp theo cho hai lỗi còn tồn tại (ngoài phạm vi 7 ngày)

Theo đúng yêu cầu của đề bài — không bắt buộc hoàn thiện nhưng phải nêu rõ
hướng giải quyết — hai lỗi dưới đây chưa được khắc phục dứt điểm trong phạm
vi 7 ngày, nhưng đã xác định được hướng kỹ thuật cụ thể:

**(a) Kịch bản 3, lượt 13 — nhầm `vessel_id` khi hành động dù vừa xác nhận
đúng tên tàu bằng lời (`results/scenario_3.md`, mục 6.4)**

Hướng đề xuất: mở rộng cơ chế pin fact từ "pin văn bản" sang "pin thực thể
đã được resolve". Hiện tại `_extract_pinned_fact` (`src/agent/memory.py`)
chỉ lưu nguyên văn câu yêu cầu ghi nhớ — model vẫn phải tự suy luận lại từ
ngôn ngữ tự nhiên để xác định "tàu đó" ứng với `vessel_id` nào ở lượt hành
động. Đề xuất cụ thể:
1. Ngay khi regex phát hiện message có nội dung yêu cầu ghi nhớ và nhắc tên
   tàu, gọi `search_vessel` để resolve tên đó thành `vessel_id` thật (dùng
   tool đã có sẵn, không bổ sung logic khớp tên mới).
2. Lưu `vessel_id` này vào một cột riêng (ví dụ
   `memory_chunks.pinned_vessel_id`, hoặc một bảng
   `conversation_focus_entity` tách biệt) thay vì chỉ lưu văn bản.
3. Ở mọi lượt tiếp theo trong cùng hội thoại, `build_llm_context` tự động
   chèn một dòng system tường minh dạng: *"vessel_id đang được theo dõi
   trong hội thoại này: `<uuid>` (tên: MSC MANYA)"* — chuyển bài toán "suy
   luận tàu đó là tàu nào" (dễ phát sinh sai sót, như đã quan sát) thành một
   giá trị tra cứu sẵn, model chỉ cần sao chép đúng UUID vào tham số tool
   thay vì tự suy luận lại từ lịch sử hội thoại.

Đánh đổi cần lưu ý: cách tiếp cận này giả định tại một thời điểm chỉ theo
dõi một thực thể chính — nếu người dùng pin nhiều tàu khác nhau trong cùng
hội thoại, cần mở rộng thành danh sách thay vì một giá trị đơn, kèm logic
xác định đúng entity đang được hỏi tới khi có nhiều pin. Trong phạm vi kịch
bản mẫu của đề bài (pin một tàu, hỏi lại đúng tàu đó), hướng đơn giản nêu
trên đã đủ giải quyết.

**(b) Kịch bản 5, lượt 3 — lựa chọn `list_vessels_by_type` thay vì
`compare_journeys` cho câu hỏi tổng hợp theo loại tàu**

Ba hướng đề xuất, có thể kết hợp:
1. **Bổ sung few-shot cụ thể trong system prompt**: quy tắc 9 hiện tại chỉ
   nêu nguyên tắc chung "dùng compare_journeys cho câu hỏi tổng hợp", chưa
   có ví dụ cụ thể đúng dạng câu hỏi tiếp nối mang ý so sánh (ví dụ "còn toàn
   bộ tàu [loại] thì sao"). Model thường bám sát few-shot cụ thể tốt hơn quy
   tắc trừu tượng — bổ sung một cặp câu hỏi/tool-call mẫu đúng dạng này vào
   `SYSTEM_PROMPT` là thay đổi có chi phí thấp, chưa được triển khai.
2. **Guardrail ở tầng agent (code, không chỉ prompt)**: sau khi model gọi
   tool, `src/agent/agent.py` có thể áp dụng một heuristic đơn giản — nếu
   câu hỏi gốc chứa từ khoá mang tính so sánh/tổng hợp ("tổng", "trung
   bình", "xa nhất", "toàn bộ"...) trong khi tool vừa gọi là
   `list_vessels_by_type`/`get_journey` (không phải `compare_journeys`), hệ
   thống tự động chèn thêm một message `system` yêu cầu model gọi lại đúng
   tool trước khi trả lời cuối, thay vì để câu trả lời chưa tối ưu được gửi
   trực tiếp cho người dùng. Cách tiếp cận này cùng triết lý với biện pháp
   đã áp dụng cho R3 — không chỉ dựa vào prompt mà bổ sung một lớp kiểm tra
   ở tầng code — chưa được triển khai do cần thêm thời gian thiết kế điều
   kiện heuristic nhằm tránh false-positive (chặn nhầm các câu hỏi hợp lệ
   khác).
3. **Thu hẹp bề mặt tool khi ngữ cảnh đang bàn về hành trình**: cân nhắc loại
   `list_vessels_by_type` khỏi danh sách tool khả dụng khi hội thoại đang
   trong luồng hỏi về hành trình/so sánh, chỉ giữ lại khi câu hỏi thuần về
   liệt kê tàu theo loại, không liên quan hành trình — nhằm giảm số lựa chọn
   dễ gây nhầm lẫn. Hướng này cần bổ sung logic phân loại ý định câu hỏi
   trước khi xác định tập tool đưa vào request, chưa được triển khai trong
   phạm vi 7 ngày.
4. **Sử dụng model có năng lực suy luận cao hơn** — vẫn là đòn bẩy có tác
   động lớn nhất khi độ chính xác được ưu tiên hơn chi phí, xem kết luận mục
   1.4 và mục 9.

## 2. Embedding

### 2.1. Các ứng viên đã cân nhắc

| Model | Đa ngôn ngữ | Số chiều | Ghi chú |
|---|---|---|---|
| `text-embedding-3-small` (OpenAI) | Có, tối ưu chính cho tiếng Anh | 1536 | Lựa chọn mặc định ban đầu trong `.env.example`, giữ để tương thích khi sử dụng OpenAI trực tiếp — yêu cầu tài khoản OpenAI riêng với LLM đang kiểm thử ở thời điểm đó |
| `bge-base-en-v1.5` | Không (thuần tiếng Anh) | 768 | Loại trừ ngay — nội dung tóm tắt hội thoại gốc có thể chứa tiếng Việt |
| `multilingual-e5-large` | Có | 1024 | Cân nhắc trên cơ sở lý thuyết, không kiểm thử — không có sẵn qua cùng provider (Cloudflare) đang sử dụng cho LLM, việc bổ sung provider thứ hai đồng nghĩa thêm một API key và một điểm rủi ro |
| Cohere `embed-multilingual-v3` | Có | 1024 | Cân nhắc trên cơ sở lý thuyết — chất lượng đa ngôn ngữ tốt theo tài liệu công khai, nhưng việc bổ sung nhà cung cấp thứ ba không cần thiết ở quy mô triển khai thử nghiệm |
| **`@cf/baai/bge-m3`** (Cloudflare) | **Có, hỗ trợ tiếng Việt** | **1024** | **Lựa chọn ban đầu** |

**Căn cứ lựa chọn `bge-m3` (ban đầu)**: hỗ trợ đa ngôn ngữ thực chất (không
chỉ tiếng Anh kèm dịch máy), cùng provider với LLM đang sử dụng — một API
key, một hoá đơn, không phát sinh thêm điểm rủi ro hạ tầng, phù hợp nguyên
tắc "ít thành phần vận hành" nêu tại mục 0.

**Cập nhật sau khi chuyển LLM sang OpenAI (mục 1.4)**: embedding được
chuyển sang `text-embedding-3-small` (OpenAI) để cùng một provider với LLM,
giữ nguyên nguyên tắc "ít thành phần vận hành". Vấn đề kỹ thuật cần xử lý:
model này có số chiều mặc định 1536, trong khi cột `memory_chunks.embedding`
trong `db/schema.sql` đã được định nghĩa `vector(1024)` (khớp `bge-m3`) —
việc đổi model khác số chiều thông thường đòi hỏi migrate schema. Giải
pháp: dòng model `text-embedding-3-*` của OpenAI hỗ trợ tham số `dimensions`
(kỹ thuật Matryoshka Representation Learning, huấn luyện để các chiều đầu
mang nhiều thông tin nhất, cho phép cắt bớt chiều sau mà không cần huấn
luyện lại) — truyền `dimensions=1024` giữ nguyên schema hiện có, không cần
migrate cơ sở dữ liệu. Đã bổ sung biến môi trường `EMBEDDING_DIMENSIONS`
(`src/utils/config.py`, `src/models/embeddings.py`), chỉ truyền tham số này
khi được cấu hình, nhằm không phá vỡ khả năng tương thích với provider không
hỗ trợ tham số đó (Cloudflare).

### 2.2. Phát hiện qua kiểm thử thực nghiệm: dải điểm similarity thấp và hẹp trên tóm tắt ngắn

**Phương pháp**: trong quá trình phát triển R3, đo cosine similarity
(`1 - (embedding <=> query)` qua pgvector) giữa câu hỏi follow-up thực tế và
các `memory_chunks` đã tóm tắt (dưới 150 từ mỗi chunk) qua nhiều lượt chạy
Kịch bản 3. Quan sát: kể cả giữa câu hỏi và đoạn tóm tắt liên quan nhất,
điểm số chỉ nằm trong khoảng 0,24–0,35 trên thang 0–1 — hẹp hơn đáng kể so
với ngưỡng thường gặp khi sử dụng embedding OpenAI (nơi ngưỡng ~0,7–0,8
thường được xem là mức liên quan).

**Hệ quả và biện pháp xử lý**: ngưỡng tuyệt đối ban đầu đặt ở mức 0,5 (theo
kinh nghiệm sử dụng embedding OpenAI) loại bỏ cả kết quả liên quan nhất —
nguyên nhân không phải chất lượng embedding kém, mà do thang điểm của
`bge-m3` trên đoạn văn ngắn vốn hẹp hơn. Ngưỡng đã được hạ xuống
`MEMORY_MIN_SIMILARITY = 0.15` (chỉ dùng để loại bỏ nhiễu rõ ràng), đồng
thời chuyển sang dựa vào thứ hạng (`ORDER BY ... LIMIT`) thay vì ngưỡng
tuyệt đối làm tiêu chí quyết định chính — phân tích nguyên nhân đầy đủ (ba
lỗi liên quan) xem mục 6.

## 3. Vector database

### 3.1. So sánh

| Lựa chọn | Ưu điểm | Hạn chế | Trường hợp phù hợp |
|---|---|---|---|
| **pgvector** (đã chọn) | Cùng Postgres đang sử dụng cho R1 (PostGIS) — không thêm service, không thêm kết nối, không thêm cơ chế đồng bộ dữ liệu giữa hai hệ thống; đủ nhanh ở quy mô vài trăm đến vài nghìn chunk mỗi hội thoại; hỗ trợ index HNSW từ pgvector ≥ 0.5 | Không chuyên biệt cho vector search ở quy mô hàng chục triệu vector — thiếu các tối ưu như quantization, sharding ngang có sẵn ở các DB chuyên dụng | Dữ liệu ứng dụng đã lưu trên Postgres, quy mô vector vừa/nhỏ, ưu tiên đơn giản hoá hạ tầng |
| Qdrant | Index HNSW tối ưu hơn cho vector thuần, khả năng filter phong phú, dashboard quản trị tốt | Thêm một service, một kết nối, cần đồng bộ ID với DB chính | Hệ thống vector-first, quy mô hàng triệu vector trở lên, cần filter phức tạp |
| Milvus | Khả năng scale ngang tốt nhất trong nhóm, thiết kế cho quy mô tỷ vector | Vận hành phức tạp nhất (nhiều thành phần: proxy, query node, data node...) — vượt mức cần thiết cho một ứng dụng chat | Quy mô rất lớn, có đội vận hành riêng cho hạ tầng dữ liệu |
| Chroma | Dễ triển khai cục bộ, phù hợp prototype nhanh | Chưa đạt tiêu chuẩn production cho quy mô hàng triệu vector, hệ sinh thái vận hành (backup, HA) còn hạn chế | Prototype/demo cá nhân, không yêu cầu tính bền vững dữ liệu nghiêm ngặt |

**Căn cứ lựa chọn pgvector**: dữ liệu tàu biển (R1) đã yêu cầu PostGIS trên
Postgres; sử dụng pgvector trên cùng cơ sở dữ liệu giảm đáng kể độ phức tạp
hạ tầng, phù hợp quy mô triển khai thử nghiệm (vài trăm đến vài nghìn chunk
mỗi hội thoại). Ở quy mô lớn hơn đáng kể (hàng triệu vector, nhiều tenant),
Qdrant/Milvus sẽ có lợi thế về hiệu năng index chuyên biệt — được ghi nhận
trong hướng mở rộng tại `docs/architecture.md`, mục 9.

## 4. Reranker

### 4.1. So sánh

| Lựa chọn | Ghi chú |
|---|---|
| **`@cf/baai/bge-reranker-base`** (đã chọn ban đầu) | Cross-encoder, cùng provider Cloudflare — không phát sinh thêm API key |
| Cohere Rerank v3 | Cân nhắc trên cơ sở lý thuyết — chất lượng đa ngôn ngữ tốt theo tài liệu công khai, nhưng bổ sung nhà cung cấp thứ ba là không cần thiết sau khi giới hạn ngôn ngữ đã được xử lý (xem mục 4.2) |
| Cross-encoder `ms-marco-MiniLM` (self-host) | Cân nhắc trên cơ sở lý thuyết — miễn phí nhưng cần tự vận hành thêm một service inference, đi ngược nguyên tắc "ít thành phần vận hành" |

### 4.2. Phát hiện qua kiểm thử thực nghiệm: reranker chỉ đạt hiệu quả tốt với tiếng Anh

**Phương pháp**: chạy cùng một tình huống truy xuất bộ nhớ (một câu hỏi và
ba đoạn văn ứng viên, trong đó chỉ một đoạn thực sự liên quan) ở hai phiên
bản ngôn ngữ — tiếng Anh và tiếng Việt — qua `bge-reranker-base`.

| Ngôn ngữ | Điểm đoạn đúng | Điểm hai đoạn còn lại | Kết quả xếp hạng |
|---|---|---|---|
| Tiếng Anh | 0,62 | 0,0001 – 0,0003 | Đúng — đoạn liên quan xếp hạng 1 rõ rệt |
| Tiếng Việt (cùng nội dung, dịch tương đương) | — | — | Không đạt — đoạn đúng xếp hạng thấp nhất trong ba lựa chọn |

**Quyết định**: `SUMMARIZE_PROMPT` (`src/agent/memory.py`) được điều chỉnh
để yêu cầu LLM tóm tắt bằng tiếng Anh, dù hội thoại gốc ở tiếng Việt. Điều
này chấp nhận được vì `memory_chunks` chỉ là dữ liệu nội bộ phục vụ LLM đọc
lại (không hiển thị trực tiếp cho người dùng) — thay đổi ngôn ngữ tóm tắt
không ảnh hưởng trải nghiệm người dùng vì câu trả lời cuối luôn bằng tiếng
Việt theo quy định của `SYSTEM_PROMPT`.

### 4.3. Cập nhật sau khi chuyển sang OpenAI: tạm thời vô hiệu hoá rerank

**Giới hạn của OpenAI**: khác với Cloudflare Workers AI (cung cấp LLM,
embedding và rerank trong cùng một nền tảng), OpenAI không có sản phẩm
rerank — API chỉ gồm chat completions, embeddings và một số sản phẩm chuyên
biệt khác (audio, image...), không có endpoint cross-encoder rerank. Do
Cloudflare cũng đồng thời hết hạn ngạch miễn phí (mục 1.4), việc tiếp tục sử
dụng `bge-reranker-base` sẽ đòi hỏi bổ sung một tài khoản/nhà cung cấp thứ
ba chỉ để phục vụ chức năng rerank, đi ngược nguyên tắc "ít thành phần vận
hành" nêu tại mục 0.

**Quyết định**: đặt `RERANKER_ENABLED=false`, quay lại sử dụng thuần
embedding similarity theo thứ hạng (không dùng ngưỡng tuyệt đối, xem mục
2.2) cho nhánh truy xuất ngữ nghĩa. Rủi ro đã biết (lỗi #3 tại mục 6.2 — khi
embedding một mình không đủ khả năng phân biệt lúc có nhiều chunk cạnh
tranh) được giảm thiểu đáng kể nhờ cơ chế pin fact tường minh bổ sung sau đó
(mục 6.3), vốn xử lý đúng trường hợp sử dụng quan trọng nhất (yêu cầu ghi
nhớ tường minh) mà không cần đến rerank. Trong trường hợp cần khôi phục
rerank mà không bổ sung nhà cung cấp mới: Cohere có gói miễn phí giới hạn
cho Rerank API, hoặc có thể tự host một cross-encoder nhỏ (`ms-marco-
MiniLM`) — xem đánh đổi self-host tại mục 9.

## 5. Framework agent

Không sử dụng LangChain/LlamaIndex/LangGraph. Vòng lặp tool-calling được
cài đặt trực tiếp (`src/agent/agent.py`, khoảng 135 dòng cho cả phiên bản
thường và phiên bản streaming).

| Lựa chọn | Ưu điểm | Hạn chế | Quyết định |
|---|---|---|---|
| LangChain | Nhiều tool tích hợp sẵn, cộng đồng lớn | Nhiều lớp trừu tượng (`AgentExecutor`, `Runnable`...) gây khó khăn khi cần giải thích tường minh từng bước; thay đổi phiên bản thường xuyên | Không sử dụng |
| LangGraph | Kiểm soát luồng tốt hơn LangChain thuần, phù hợp agent có nhánh phức tạp | Chi phí học tập và giải thích lớn hơn nhiều so với lợi ích mang lại cho một luồng tuyến tính (gọi LLM, gọi tool, lặp lại) | Không sử dụng |
| CrewAI/AutoGen (multi-agent) | Phù hợp cho bài toán nhiều agent phối hợp | Bài toán này chỉ có một agent, một luồng xử lý — sử dụng framework multi-agent là không cần thiết | Không sử dụng |
| **Tự cài đặt vòng lặp** | Tường minh hoàn toàn, dễ debug (đã chứng minh qua việc xác định nguyên nhân gốc của ba lỗi liên quan đến R3 một cách nhanh chóng), không phụ thuộc phiên bản của framework ngoài | Phải tự cài đặt các tiện ích mà framework thường cung cấp sẵn (retry, streaming parser...) | **Đã chọn** |

**Căn cứ lựa chọn (bám sát yêu cầu đề bài)**: đề bài quy định mọi phần
trong tài liệu mô tả phải được giải thích được, kể cả khi có sử dụng
framework hoặc trợ lý AI hỗ trợ. Với chín tool và một luồng xử lý tuyến tính
(gọi LLM, nếu có tool_call thì thực thi tool, đưa kết quả trở lại, lặp lại),
lợi ích của một framework agent phức tạp (orchestration nhiều lớp, đa agent,
đồ thị có nhánh...) là không cần thiết, trong khi chi phí phải giải thích
toàn bộ lớp trừu tượng bên trong framework đó là chi phí thực tế cần cân
nhắc.

## 6. So sánh chiến lược bộ nhớ dài hạn (R3)

### 6.1. Ma trận so sánh

| Chiến lược | Độ chính xác dài hạn | Chi phí bổ sung | Độ trễ bổ sung | Độ phức tạp | Rủi ro |
|---|---|---|---|---|---|
| Cửa sổ trượt (sliding window) thuần | Rất thấp — mất hoàn toàn thông tin ngoài cửa sổ | Không | Không | Rất thấp | Cao khi hội thoại vượt cửa sổ (Kịch bản 3 sẽ luôn không đạt) |
| Tóm tắt (summarization) thuần | Trung bình — phụ thuộc chất lượng tóm tắt, có thể bỏ sót chi tiết | Thấp (một lần gọi LLM tóm tắt) | Thấp | Thấp | Model tóm tắt có thể bỏ sót đúng thông tin cần ghi nhớ (đã quan sát thực tế, xem mục 6.2, lỗi #1) |
| Truy xuất vector (embedding retrieval) thuần | Trung bình đến cao, phụ thuộc chất lượng embedding | Trung bình (nhúng và truy vấn mỗi lượt) | Trung bình | Trung bình | Hiệu quả kém khi nhiều chunk ngắn/tương tự cạnh tranh điểm số sát nhau (đã quan sát thực tế, xem mục 6.2, lỗi #3) |
| Kết hợp (sliding window + tóm tắt + embedding + rerank) | Cao hơn từng phương án riêng lẻ, nhưng chưa đạt độ chính xác tuyệt đối với model 20B khi hội thoại rất dài | Cao nhất (tóm tắt, nhúng và rerank mỗi lượt) | Cao nhất | Cao — nhiều điểm có khả năng phát sinh lỗi | Đã ghi nhận cả ba lỗi (mục 6.2) — mỗi lớp bổ sung giảm một loại lỗi nhưng làm hệ thống khó debug hơn |
| **Kết hợp + pin fact tường minh** (bổ sung sau đánh giá) | Cao nhất trong các phương án đã kiểm thử — tách riêng yêu cầu ghi nhớ tường minh khỏi ngữ cảnh chung | Thấp (chỉ bổ sung một regex và một cột boolean, không thêm lời gọi model) | Không đáng kể | Trung bình (bổ sung một nhánh logic, không thêm service) | Phụ thuộc khả năng của regex trigger trong việc nhận diện đúng câu yêu cầu ghi nhớ — xem giới hạn tại mục 6.3 |

### 6.2. Ba lỗi phát hiện được khi kiểm thử R3 bằng LLM thực tế

Kiểm chứng qua Kịch bản 3 (13 lượt, `CONTEXT_WINDOW_TURNS=6` tại thời điểm
kiểm thử), chạy trực tiếp nhiều lần trong quá trình phát triển:

| # | Triệu chứng | Nguyên nhân gốc | Biện pháp khắc phục | Xác nhận |
|---|---|---|---|---|
| 1 | Bản tóm tắt bỏ sót mã hồ sơ (`HS-2026-117`) dù văn bản gốc có đầy đủ | LLM tóm tắt ưu tiên các chi tiết kỹ thuật khác (thông số tàu) xuất hiện cùng đoạn, bỏ qua câu yêu cầu ghi nhớ vì không được nhấn mạnh trong prompt tóm tắt | Điều chỉnh `SUMMARIZE_PROMPT`: yêu cầu rõ rằng nếu người dùng đề nghị ghi nhớ, thông tin đó phải được liệt kê tường minh, không được bỏ qua để ưu tiên chi tiết khác | Unit test `tests/test_memory.py`, xác nhận qua LLM thực tế |
| 2 | Ngưỡng similarity 0,5 loại bỏ cả chunk đúng nhất | Điểm cosine của `bge-m3` trên đoạn tóm tắt ngắn vốn hẹp tự nhiên (0,24–0,35, xem mục 2.2) — ngưỡng 0,5 cao hơn cả điểm của chunk liên quan nhất | Hạ `MEMORY_MIN_SIMILARITY` xuống 0,15, chuyển sang dùng thứ hạng thay vì ngưỡng tuyệt đối | Xác nhận qua LLM thực tế |
| 3 | Khi hội thoại có từ 11 chunk cạnh tranh trở lên, embedding một mình không đủ khả năng phân biệt — chunk đúng bị loại khỏi top-3 | Nhiều chunk có điểm số sát nhau (0,24–0,35) do bản chất thang điểm hẹp | Bổ sung rerank (cross-encoder `bge-reranker-base`) sau bước lọc similarity | Một lần chạy độc lập đạt 2/2, xem phân tích tiếp theo |

**Kết quả sau ba biện pháp khắc phục**: một lần chạy riêng đạt 2/2, nhưng
một lần chạy đầy đủ khác (cùng lúc với bốn kịch bản còn lại) cho kết quả
0/2 — model nhầm sang tàu vừa được nhắc gần nhất thay vì tàu đã được yêu cầu
ghi nhớ ở lượt 1. Kết luận tại thời điểm đó: ba biện pháp khắc phục là đúng
và cần thiết, nhưng cơ chế "kết hợp" thuần (tóm tắt, embedding, rerank) vẫn
phụ thuộc vào khả năng model 20B tham số tự ưu tiên đúng ngữ cảnh trong một
khối văn bản dài — đây là giới hạn mang tính xác suất, không phải lỗi có
thể khắc phục dứt điểm bằng cách điều chỉnh tham số.

### 6.3. Giải pháp bổ sung sau đánh giá: pin fact tường minh

Thay vì tiếp tục điều chỉnh tham số của cơ chế "kết hợp" (đã chạm giới hạn
nêu tại mục 6.2), hướng khắc phục được lựa chọn là tách riêng lớp "yêu cầu
ghi nhớ tường minh" khỏi lớp "tóm tắt ngữ nghĩa nói chung":

- Khi một message của người dùng khớp regex nhận diện câu yêu cầu ghi nhớ
  (`ghi nho|nho giup|nho ho|hay nho|nho rang`, so khớp trên bản không dấu để
  bắt cả hai dạng có dấu/không dấu), toàn văn message đó được lưu thành một
  fact riêng (`memory_chunks.is_pinned = true`), không đi qua bước tóm tắt
  của LLM.
- Khi xây dựng context cho lượt tiếp theo, mọi fact có `is_pinned = true`
  của hội thoại đó luôn được đưa vào, không phụ thuộc điểm similarity/rerank
  — loại bỏ hoàn toàn nguyên nhân gốc của lỗi #2 và #3 (ngưỡng điểm, cạnh
  tranh giữa nhiều chunk) đối với loại thông tin quan trọng nhất.
- Đánh đổi: cơ chế regex chỉ nhận diện được câu nói theo mẫu tường minh
  ("ghi nhớ giúp tôi..."); nếu người dùng diễn đạt theo cách khác không sử
  dụng các từ khoá trên, fact đó vẫn đi qua đường tóm tắt ngữ nghĩa thông
  thường (mục 6.1, dòng "Kết hợp"), với độ tin cậy như đã ghi nhận tại mục
  6.2. Đây là đánh đổi có chủ đích: ưu tiên độ chính xác gần như tuyệt đối
  cho đúng trường hợp sử dụng được nêu rõ trong kịch bản mẫu của đề bài
  (Kịch bản 3, lượt 1: *"Ghi nhớ giúp tôi: tôi phụ trách hồ sơ..."*), chấp
  nhận rủi ro dư ở mức thấp hơn đối với trường hợp sử dụng nằm ngoài phạm vi
  kịch bản mẫu.

**Kết quả sau khi bổ sung cơ chế pin**: chạy lại đầy đủ năm kịch bản mẫu qua
LLM thực tế, kiểm chứng bằng `scripts/verify_results.py` — Kịch bản 3, lượt
12 và 13 đạt yêu cầu (transcript: `results/scenario_3.md`), tổng thể 13/13
(100%) các mục kiểm chứng tự động trên cả năm kịch bản
(`results/verify_summary.txt`). Ghi chú: đây là kết quả của một lần chạy
đầy đủ; do bản chất không xác định của LLM, không có gì đảm bảo kết quả
tương tự ở mọi lần chạy — tuy nhiên khác với cơ chế "kết hợp" thuần (phụ
thuộc hoàn toàn vào lựa chọn ngữ cảnh của model), cơ chế pin loại bỏ hẳn một
lớp bất định (điểm similarity/rerank) đối với đúng loại câu hỏi mà kịch bản
mẫu kiểm tra, nên có cơ sở kỳ vọng ổn định hơn về mặt lý thuyết.

### 6.4. Phát hiện với `gpt-4o-mini`: pin fact giải quyết việc nhắc lại bằng lời, chưa giải quyết bước hành động

Sau khi chuyển sang `gpt-4o-mini` (mục 1.4) và chạy lại Kịch bản 3, một biến
thể mới của cùng loại lỗi "nhầm tàu vừa nhắc gần nhất" được ghi nhận, nằm
ngoài phạm vi bao phủ của cơ chế pin fact (mục 6.3):

- **Lượt 12** ("Hồ sơ tôi nhắc từ đầu... đang theo dõi tàu nào?"): trả lời
  đúng bằng lời — "đang theo dõi tàu MSC MANYA" — cơ chế pin fact hoạt động
  chính xác, đạt yêu cầu.
- **Lượt 13** ("Vị trí cuối cùng... của tàu đó"): gọi đúng tool
  (`get_position_at_time`, không kèm `at_ts`, sử dụng đúng cơ chế "vị trí
  mới nhất" — xem `docs/architecture.md`, mục 7), nhưng truyền `vessel_id`
  của TENGXIANHAIXIANG77 — tàu được hỏi ở lượt 11, tàu gần nhất về thứ tự
  lời gọi tool — thay vì `vessel_id` của MSC MANYA, tàu vừa được chính model
  xác nhận đúng ở lượt 12 ngay trước đó. Không đạt yêu cầu.

**Phân tích**: cơ chế pin fact (mục 6.3) đảm bảo thông tin MSC MANYA luôn có
mặt trong context (giải quyết được việc nhắc lại đúng bằng lời ở lượt 12),
nhưng không có cơ chế nào ràng buộc bước hành động (lựa chọn `vessel_id` để
gọi tool) ở lượt kế tiếp phải sử dụng đúng thực thể vừa được nhắc — model có
xu hướng ưu tiên "tàu gần nhất trong lịch sử tool-calling" hơn "tàu vừa được
nêu tên trong chính câu trả lời của nó". Đây là lỗi suy luận/liên kết ngữ
cảnh, không phải lỗi truy xuất bộ nhớ — nằm ngoài phạm vi mà cơ chế pin fact
có thể xử lý, do cơ chế này chỉ đảm bảo dữ liệu có mặt trong context, không
đảm bảo model sử dụng đúng dữ liệu đó khi hành động.

**Biện pháp đã áp dụng**: bổ sung một quy tắc cụ thể vào `SYSTEM_PROMPT`
(quy tắc 6, `src/prompts/system_prompts.py`) yêu cầu model đối chiếu
`vessel_id` truyền vào tool với tên tàu vừa nêu trong câu trả lời liền
trước. Đây là biện pháp giảm xác suất ở tầng prompt, không phải khắc phục
dứt điểm, nhất quán với kết luận chung của toàn mục 6: mọi cơ chế đều có
giới hạn độ tin cậy phụ thuộc vào năng lực suy luận của model đang sử dụng —
model nhỏ/chi phí thấp hơn (dù tool-calling format ổn định) vẫn có khả năng
mắc lỗi liên kết ngữ cảnh mà model có năng lực suy luận cao hơn ít gặp phải
hơn. Hướng khắc phục kỹ thuật cụ thể (mở rộng pin fact sang pin thực thể đã
resolve, chưa triển khai trong phạm vi 7 ngày) được trình bày tại mục
1.5(a). Xem thêm mục 9 về đánh đổi self-host khi cần độ tin cậy cao hơn.

## 7. Framework backend

FastAPI kết hợp PostgreSQL/PostGIS và Docker Compose, theo đúng gợi ý của
đề bài. Một số quyết định bổ sung không nằm trong gợi ý gốc:

| Quyết định | Căn cứ |
|---|---|
| SSE (`StreamingResponse`) thay vì WebSocket | Giao tiếp chat trong hệ thống này về bản chất là một chiều theo lượt (client gửi một message, server trả về một luồng sự kiện rồi đóng) — không cần kênh hai chiều liên tục của WebSocket. SSE đơn giản hơn (không cần quản lý handshake/ping-pong riêng), FastAPI hỗ trợ tốt qua `StreamingResponse`, và có thể debug trực tiếp bằng `curl -N` (đáp ứng yêu cầu D1) mà không cần client WebSocket riêng |
| PostgreSQL kết hợp PostGIS thay vì MongoDB/Elasticsearch cho dữ liệu không gian | PostGIS là lựa chọn tiêu chuẩn ngành cho dữ liệu địa lý quan hệ (index GiST, hệ hàm `ST_*` phong phú, hỗ trợ kiểu `geography` cho tính khoảng cách chính xác trên mặt cầu) — geo-index của MongoDB đơn giản hơn nhưng thiếu các phép tính hình học phức tạp (`ST_Simplify`, `ST_MakeLine` có `ORDER BY`) mà N2/N3 yêu cầu |
| Một cơ sở dữ liệu cho cả dữ liệu tàu biển, hội thoại và vector | Xem mục 3 — giảm số lượng service cần vận hành trong phạm vi 7 ngày |

## 8. Bảng tổng hợp lựa chọn hiện hành

Đã có một lần điều chỉnh sau đánh giá (căn cứ đầy đủ tại mục 1.4) — bảng
dưới đây phản ánh trạng thái đang triển khai, không phải lựa chọn ban đầu
(`gpt-oss-20b`, `bge-m3`, `bge-reranker-base` qua Cloudflare). Quá trình và
căn cứ của lựa chọn ban đầu vẫn được giữ nguyên ở các mục trên vì đó là bằng
chứng quan trọng cho quá trình ra quyết định.

| Thành phần | Lựa chọn hiện hành | Lựa chọn ban đầu | Lý do điều chỉnh |
|---|---|---|---|
| LLM | `gpt-4o-mini` (OpenAI) | `gpt-oss-20b` (Cloudflare) | Cloudflare hết hạn ngạch miễn phí trong quá trình kiểm thử; OpenAI không đòi hỏi thay đổi code (mục 1.4) |
| Embedding | `text-embedding-3-small`, `dimensions=1024` (OpenAI) | `bge-m3` (Cloudflare) | Cùng provider với LLM mới; giữ nguyên schema `vector(1024)` nhờ tham số `dimensions` |
| Vector DB | pgvector (không đổi) | pgvector | Không thêm service, đủ nhanh ở quy mô triển khai thử nghiệm |
| Reranker | Vô hiệu hoá (`RERANKER_ENABLED=false`) | `bge-reranker-base` (Cloudflare) | OpenAI không có sản phẩm rerank; được bù đắp bằng cơ chế pin fact (mục 4.3, 6.3) |
| Chiến lược bộ nhớ | Kết hợp + pin fact tường minh (không đổi) | — | Phương án đạt tỷ lệ kiểm chứng cao nhất qua LLM thực tế |
| Framework agent | Tự cài đặt (~135 dòng, không đổi) | — | Bám sát yêu cầu giải thích được mọi phần |
| Backend | FastAPI, SSE, PostgreSQL/PostGIS, Docker Compose (không đổi) | — | Đúng gợi ý đề bài, SSE đáp ứng đủ nhu cầu giao tiếp một chiều theo lượt |

## 9. Hướng self-host khi có hạ tầng riêng

Toàn bộ lựa chọn LLM/embedding/rerank nêu trên đều là managed API (tính phí
theo token, không quản lý hạ tầng). Đây là lựa chọn hợp lý cho một bài toán
triển khai 7 ngày thực hiện độc lập, nhưng khi có hạ tầng riêng (máy chủ
GPU) và bài toán vận hành dài hạn ở quy mô lớn hơn, hướng self-host (triển
khai model mở qua vLLM/TGI/Ollama trên GPU riêng) đáng được cân nhắc
nghiêm túc. Dưới đây là các điểm mạnh cụ thể, đối chiếu với những vấn đề đã
phát sinh trong thực tế quá trình triển khai:

| Điểm mạnh của self-host | Đối chiếu với vấn đề thực tế đã phát sinh |
|---|---|
| **Không giới hạn hạn ngạch/rate limit** | Đây chính là nguyên nhân dẫn đến việc phải chuyển provider giữa quá trình triển khai (mục 1.4) — Cloudflare hết 10.000 neurons/ngày ở gói miễn phí. Self-host trên GPU riêng không có khái niệm hạn ngạch theo ngày, chỉ giới hạn bởi throughput phần cứng sẵn có |
| **Chi phí biên tiệm cận 0 sau đầu tư ban đầu** | Ở quy mô triển khai thử nghiệm, chi phí API không đáng kể (xem `docs/architecture.md`, mục 8.2) — nhưng ở quy mô production (hàng chục nghìn lượt/ngày), chi phí API tăng tuyến tính theo token, trong khi GPU tự vận hành có chi phí cố định (khấu hao, điện năng) không đổi theo lượng sử dụng, dẫn đến điểm hoà vốn đạt nhanh ở tải cao |
| **Không phụ thuộc uptime của bên thứ ba** | Sự cố lỗi 500 kéo dài của Cloudflare ở Kịch bản 5 (mục 1.3) là ví dụ thực tế — self-host loại bỏ hoàn toàn phụ thuộc vào SLA của nhà cung cấp ngoài, đổi lại là trách nhiệm tự vận hành uptime |
| **Kiểm soát dữ liệu và quyền riêng tư** | Dữ liệu AIS/đăng kiểm/chủ sở hữu tàu trong bài toán này không đặc biệt nhạy cảm, nhưng ở ứng dụng thực tế (ví dụ dữ liệu vận hành của một hãng tàu), việc dữ liệu không rời khỏi hạ tầng riêng có thể là yêu cầu bắt buộc về tuân thủ |
| **Toàn quyền lựa chọn tool-call parser/định dạng phù hợp** | Nguyên nhân khiến `qwen3.5-9b` không đạt yêu cầu (mục 1.2) là do server vLLM tự host thiếu cấu hình `--tool-call-parser` — đây là hạn chế của self-host (phải tự cấu hình đúng), nhưng đồng thời cũng là điểm mạnh: khi cấu hình đúng, có toàn quyền lựa chọn/thay đổi model mà không bị ràng buộc vào một định dạng hay nhà cung cấp |
| **Có thể tự host reranker không phụ thuộc danh mục sản phẩm của nhà cung cấp** | Đúng vấn đề đã phát sinh tại mục 4.3 — OpenAI không có sản phẩm rerank, buộc phải vô hiệu hoá hoặc tìm nhà cung cấp thứ ba. Self-host cross-encoder (`bge-reranker-base`, `ms-marco-MiniLM`...) chạy trực tiếp trên GPU riêng, không phụ thuộc việc một API có cung cấp tính năng đó hay không |
| **Khả năng tinh chỉnh/fine-tune cho đúng domain** | Không cần thiết ở quy mô triển khai thử nghiệm, nhưng khi dữ liệu tàu biển mở rộng lâu dài, có thể fine-tune model mở cho đúng thuật ngữ hàng hải và định dạng trả lời mong muốn — không khả thi với model đóng qua API |
| **Độ trễ có thể dự đoán và kiểm soát** | Managed API cộng thêm độ trễ mạng và hàng đợi phía nhà cung cấp (biến thiên, ngoài tầm kiểm soát); self-host trên phần cứng riêng, cùng mạng nội bộ, cho độ trễ ổn định hơn — quan trọng khi cần đảm bảo SLA chặt cho ứng dụng thời gian thực |

**Đánh đổi cần nêu rõ**: self-host chuyển toàn bộ trách nhiệm vận hành
(uptime, bảo mật, nâng cấp, giám sát GPU) từ nhà cung cấp sang đội ngũ nội
bộ. Sự cố thực tế với `qwen3.5-9b` (thiếu một dòng cấu hình
`--tool-call-parser` khiến toàn bộ tool-calling không hoạt động mà không có
cảnh báo — mục 1.2) là ví dụ cụ thể cho thấy self-host đòi hỏi năng lực vận
hành hạ tầng inference đúng đắn, không đơn thuần là triển khai model lên
GPU. Với phạm vi triển khai 7 ngày thực hiện độc lập và không có sẵn máy chủ
GPU, managed API vẫn là lựa chọn phù hợp — hướng self-host chỉ nên được cân
nhắc khi đã có hạ tầng và đội ngũ vận hành tương ứng.
