# Kịch bản video demo portfolio — HMS AI Copilot

## 1. Mục tiêu video

- Thời lượng mục tiêu: **6 phút 30 giây đến 7 phút 30 giây**.
- Đối tượng xem: recruiter, engineering manager, backend/AI engineer.
- Thông điệp chính: đây không chỉ là một giao diện chatbot; dự án giải quyết bài toán đưa AI vào dữ liệu bệnh viện với **kiểm soát quyền trước retrieval, câu trả lời có nguồn, Graph RAG có provenance, pipeline xử lý tài liệu bất đồng bộ và audit trail**.
- Chỉ sử dụng **dữ liệu synthetic/de-identified**. Giữ nhãn `Synthetic Data` xuất hiện trong khung hình.

## 2. Bốn phần nên ưu tiên demo

1. **Patient-scoped RAG có citation** — phần mạnh nhất vì thể hiện đồng thời AI, backend và an toàn dữ liệu.
2. **Patient Knowledge Graph** — trực quan, dễ tạo ấn tượng và cho thấy quan hệ giữa chẩn đoán, thuốc, xét nghiệm và nguồn chứng cứ.
3. **OCR → chunk → embedding → indexing** — chứng minh hệ thống có pipeline dữ liệu, không chỉ có màn hình chat.
4. **Permission denial + audit** — tạo khác biệt so với chatbot demo thông thường và cho thấy tư duy hệ thống y tế.

Không nên dành nhiều thời gian cho dashboard, settings hoặc các màn hình CRUD thông thường.

## 3. Chuẩn bị trước khi quay

### Dữ liệu và tài khoản

- Đăng nhập vai trò **Cardiologist — Dr. Sarah Chen** cho phần bệnh nhân và chat.
- Dùng bệnh nhân **Alice Synthetic — MRN-0001**.
- Bảo đảm Alice đã có ít nhất một tài liệu indexed và một số quan hệ Graph RAG.
- Chuẩn bị một PDF synthetic ngắn, ví dụ `alice-synthetic-lab-result.pdf`. Tuyệt đối không dùng hồ sơ thật.
- Chuẩn bị vai trò **Security Auditor — Sam Security** cho phần audit.

### Câu hỏi dùng trong chat

Sử dụng câu đã có trong UAT của dự án:

> What is the appointment status and vital signs?

Câu dự phòng nếu dữ liệu seed hiện tại khác:

> Summarize the latest documented clinical facts for this patient and cite every source.

### Các tab nên mở sẵn

1. Patient Overview của Alice Synthetic.
2. Patient Chat của Alice Synthetic.
3. Patient Knowledge Graph.
4. Documents / OCR queue.
5. Audit Logs ở vai trò Security.

### Quy tắc quay

- Quay ở 1080p, zoom trình duyệt 100–110%, tắt notification của hệ điều hành.
- Sau mỗi click, dừng khoảng 1 giây để người xem nhìn thấy thay đổi.
- Không cuộn quá nhanh và không đọc toàn bộ nội dung trên màn hình.
- Nếu AI phản hồi chậm, cắt khoảng chờ nhưng giữ lại các trạng thái `retrieving`, `preparing answer`, `validating citations`.
- Không quay URL chứa token, file `.env`, terminal có secret hoặc dữ liệu ngoài bộ synthetic.

## 4. Kịch bản chi tiết

### Cảnh 1 — Hook và bài toán (0:00–0:30)

**Màn hình**

- Mở Patient Overview của Alice Synthetic.
- Giữ nhãn `Synthetic Data`, vai trò `Cardiologist` và trạng thái `Allowed` trong khung hình.

**Lời nói**

> Đây là HMS AI Copilot, một hệ thống trợ lý tri thức bệnh viện full-stack mà tôi xây dựng để giải quyết một vấn đề khó hơn chatbot thông thường: làm sao cho AI trả lời từ hồ sơ lâm sàng mà vẫn kiểm soát đúng bệnh nhân, đúng quyền truy cập và đúng nguồn chứng cứ.
>
> Toàn bộ dữ liệu trong video là dữ liệu synthetic. Trong vài phút tới, tôi sẽ demo bốn luồng chính: patient-scoped RAG, citation validation, Graph RAG và pipeline OCR có audit trail.

**Điểm cần nhấn trên màn hình**

- `Alice Synthetic`.
- `Allowed` hoặc `Access verified`.
- `AI clinical summary`.

---

### Cảnh 2 — Hồ sơ bệnh nhân hợp nhất (0:30–1:05)

**Thao tác**

1. Di chuột qua các tab `Overview`, `Timeline`, `Labs`, `Medications`, `Documents`.
2. Mở nhanh `Timeline`, sau đó quay lại `Overview`.
3. Bấm `Open chat`.

**Lời nói**

> Ở patient workspace, bác sĩ nhìn thấy dữ liệu theo từng miền như timeline, xét nghiệm, thuốc và tài liệu. Nhưng giá trị chính không nằm ở việc hiển thị nhiều tab; hệ thống dùng patient context này làm ranh giới authorization cho toàn bộ retrieval phía sau.
>
> Trước khi bất kỳ chunk tài liệu nào được đưa vào ngữ cảnh của mô hình, backend kiểm tra quyền đọc trên đúng patient ID. Nếu quyền đã hết hạn hoặc không tồn tại, request bị từ chối và một audit event được ghi lại.

**Chuyển cảnh**

> Bây giờ tôi sẽ hỏi một câu cần kết hợp dữ liệu bệnh nhân với nguồn đã được index.

---

### Cảnh 3 — Patient-scoped RAG và citation validation (1:05–2:45)

**Thao tác**

1. Xác nhận chip `Context: Patient — Alice Synthetic` đang hiện.
2. Nhập:

   `What is the appointment status and vital signs?`

3. Bấm `Send`.
4. Giữ khung hình ở các trạng thái xử lý.
5. Khi câu trả lời xuất hiện, trỏ vào citation và mở nguồn chứng cứ.
6. Nếu có trang compare citations, mở hai passage cạnh nhau trong 5–8 giây.

**Lời nói trong lúc nhập câu hỏi**

> Câu hỏi này chạy trong patient-linked thread, nên retrieval không được phép lấy dữ liệu của bệnh nhân khác, kể cả khi nội dung có độ tương đồng cao hơn.

**Lời nói trong lúc hệ thống xử lý**

> Pipeline đang retrieve evidence, chuẩn bị câu trả lời và xác thực citation. Một chi tiết kỹ thuật quan trọng là backend không phát câu trả lời ra client ngay khi LLM tạo token. Kết quả được giữ lại để output guardrail và citation validator kiểm tra trước.

**Lời nói khi câu trả lời xuất hiện**

> Chỉ khi mọi citation đều ánh xạ tới evidence đã được retrieval và đã qua authorization thì câu trả lời mới được gửi tới giao diện. Phần citation trả về cũng chỉ chứa những evidence thực sự được dùng trong câu trả lời, kèm document, page và confidence.
>
> Nếu hệ thống không có đủ bằng chứng, hoặc mô hình tạo một citation không tồn tại, hệ thống chọn safe refusal thay vì trả lời phỏng đoán. Với dữ liệu y tế, tôi ưu tiên một câu từ chối có kiểm soát hơn một câu trả lời nghe hợp lý nhưng không kiểm chứng được.

**Không nói**

- Không nói “token được stream trực tiếp từ LLM”. Source hiện tại buffer nội dung trước khi phát để bảo đảm an toàn.
- Không nói “đã loại bỏ hoàn toàn hallucination”. Hãy nói “citation không hợp lệ bị chặn trước khi tới client”.

---

### Cảnh 4 — Graph RAG có provenance (2:45–3:50)

**Thao tác**

1. Mở `Graph RAG` → `Patient knowledge graph`.
2. Dừng 2 giây ở tổng số entities và edges.
3. Click lần lượt một node diagnosis, medication và lab.
4. Chỉ vào nhãn quan hệ như `treats`, `indicated_by` hoặc quan hệ đang có trong dữ liệu.
5. Chỉ vào `Reasoning path` và dòng evidence chứa document/chunk provenance.

**Lời nói**

> Ngoài vector retrieval, hệ thống còn xây dựng một patient knowledge graph từ các tài liệu đã index. Các entity như chẩn đoán, thuốc và xét nghiệm được nối bằng quan hệ lâm sàng để hỗ trợ câu hỏi nhiều bước.
>
> Điểm tôi muốn nhấn mạnh không chỉ là hình graph. Endpoint này kiểm tra patient permission trước, sau đó chỉ dựng graph từ document, page và chunk còn active, cùng patient ID và đã đi qua visibility filter.
>
> Mỗi reasoning edge giữ provenance về document và chunk nguồn. Vì vậy graph không phải một sơ đồ do UI tự tạo; người dùng có thể truy ngược quan hệ về evidence đã tạo ra nó.

**Lưu ý quay**

- Không bật query parameter hoặc nút mô phỏng `stream-fail` trong video chính.
- Nếu graph chưa có relation, không quay placeholder graph. Seed/index lại dữ liệu trước khi quay.

---

### Cảnh 5 — Pipeline tài liệu OCR và indexing (3:50–5:05)

**Thao tác**

1. Mở `Documents` → `Upload`.
2. Chọn Alice Synthetic, nhập tiêu đề và upload PDF synthetic đã chuẩn bị.
3. Chuyển sang `OCR processing queue`.
4. Chỉ vào các trạng thái `Queued`, `Processing`, `Review`, `Indexed` và cột confidence.
5. Nếu job hoàn thành đủ nhanh, mở document detail để xem timeline xử lý và preview trang.
6. Có thể cắt thời gian chờ, nhưng giữ đúng thứ tự sự kiện.

**Lời nói**

> Dữ liệu RAG không được hard-code vào chat. Tài liệu đi qua một background pipeline: lưu file, trích xuất text, ghi page và OCR confidence, chia chunk, tạo embedding, chuẩn bị BM25 search vector, sau đó trích xuất entity và relation cho Graph RAG.
>
> Với PDF có text, hệ thống ưu tiên native text extraction. Với trang chỉ có ảnh, PaddleOCR được dùng khi OCR dependency được cài đặt. Vì vậy trong portfolio tôi mô tả đây là một pipeline có OCR fallback, không tuyên bố độ chính xác OCR nếu chưa chạy benchmark CER và WER trên bộ scan chuẩn.
>
> Mỗi attempt có processing events riêng. Khi index thành công, hệ thống tăng generation và lưu source hash. Cơ chế này giúp tránh ghi đè index cũ bằng một worker stale hoặc một lần re-index thất bại.

**Điểm kỹ thuật nên hiện bằng subtitle ngắn**

`PDF/Image → OCR/Text → Pages → Chunks → Embeddings/BM25 → Graph entities → Indexed`

---

### Cảnh 6 — Permission denial và audit trail (5:05–6:10)

**Thao tác**

1. Ở vai trò Cardiologist, thử mở `Audit Logs` để hiện màn hình 403.
2. Dừng ở thông báo không đủ quyền và reference/audit ID.
3. Chuyển sang vai trò `Security Auditor`.
4. Mở `Audit Logs`, lọc `Outcome = denied` nếu dữ liệu hiện tại hỗ trợ.
5. Mở một event để cho thấy actor, action, patient/object, outcome và trace ID.

**Lời nói**

> Giao diện cũng phản ánh separation of duties. Bác sĩ có thể dùng dữ liệu bệnh nhân được cấp quyền, nhưng không thể đọc audit log toàn hệ thống.
>
> Khi chuyển sang Security Auditor, tôi có thể xem các sự kiện denied và trace chúng theo actor, action, patient hoặc object. Ở backend, audit log chỉ mở cho Security hoặc Admin; các lần patient-scope denial được ghi trước khi trả về lỗi 403.
>
> Luồng này cho thấy authorization không chỉ là ẩn một menu ở frontend. Quyết định cuối cùng vẫn được enforcement ở API và retrieval layer.

---

### Cảnh 7 — Engineering proof và kết thúc (6:10–7:00)

**Màn hình**

- Chia đôi màn hình: bên trái là giao diện chat/graph, bên phải là IDE.
- Chỉ lướt qua ba đoạn source, không đọc từng dòng:
  1. `PermissionService.require_patient_scope`.
  2. citation validation trong `chat_stream.py`.
  3. `process_document` trong worker.

**Lời nói**

> Về kiến trúc, frontend được xây bằng TanStack Start và React; backend dùng FastAPI, SQLAlchemy, PostgreSQL với pgvector, cùng Redis/RQ cho background jobs.
>
> Phần tôi tập trung nhiều nhất không phải là gọi một LLM API, mà là các contract xung quanh nó: permission trước retrieval, evidence có vòng đời rõ ràng, citation được xác thực, sync và streaming giữ cùng nguyên tắc an toàn, và mọi quyết định quan trọng đều có trace.
>
> Đây là một dự án engineering portfolio đang tiếp tục được đánh giá bằng các harness riêng cho chat, retrieval, Graph RAG và OCR. Source code, kiến trúc và hướng dẫn chạy được đính kèm trong portfolio. Cảm ơn bạn đã xem.

## 5. Bản lời nói liền mạch

> Đây là HMS AI Copilot, một hệ thống trợ lý tri thức bệnh viện full-stack mà tôi xây dựng để giải quyết một vấn đề khó hơn chatbot thông thường: làm sao cho AI trả lời từ hồ sơ lâm sàng mà vẫn kiểm soát đúng bệnh nhân, đúng quyền truy cập và đúng nguồn chứng cứ. Toàn bộ dữ liệu trong video là dữ liệu synthetic.
>
> Ở patient workspace, bác sĩ nhìn thấy timeline, xét nghiệm, thuốc và tài liệu. Patient context này đồng thời là ranh giới authorization cho retrieval. Trước khi bất kỳ chunk nào được đưa vào ngữ cảnh của mô hình, backend kiểm tra quyền đọc trên đúng patient ID. Nếu quyền không tồn tại hoặc đã hết hạn, request bị từ chối và một audit event được ghi lại.
>
> Tôi sẽ hỏi: “What is the appointment status and vital signs?”. Đây là một patient-linked thread, vì vậy retrieval không được lấy dữ liệu của bệnh nhân khác dù nội dung của họ có thể tương đồng hơn.
>
> Pipeline đang retrieve evidence, chuẩn bị câu trả lời và xác thực citation. Backend giữ lại output để chạy guardrail và kiểm tra rằng mọi citation đều thuộc tập evidence đã được retrieval và authorization. Chỉ những evidence thực sự được trích dẫn mới được gửi ra giao diện. Nếu không đủ bằng chứng hoặc citation không hợp lệ, hệ thống trả về safe refusal thay vì phỏng đoán.
>
> Ngoài vector retrieval, hệ thống xây dựng patient knowledge graph từ các tài liệu đã index. Các entity như chẩn đoán, thuốc và xét nghiệm được liên kết để hỗ trợ câu hỏi nhiều bước. Graph endpoint vẫn kiểm tra patient permission, chỉ dùng document, page và chunk còn active, đồng thời giữ provenance về document và chunk cho từng reasoning edge.
>
> Dữ liệu này không được hard-code vào chatbot. Khi upload một tài liệu synthetic, background worker trích xuất text hoặc dùng OCR fallback, ghi page và confidence, chia chunk, tạo embedding, chuẩn bị BM25 search vector, rồi trích xuất entity và relation cho Graph RAG. Mỗi attempt có processing events, generation và source hash để tránh worker stale ghi đè dữ liệu hợp lệ.
>
> Giao diện cũng phản ánh separation of duties. Cardiologist không thể đọc audit log toàn hệ thống. Security Auditor mới có quyền xem các sự kiện denied theo actor, action, patient hoặc trace ID. Authorization vì vậy không chỉ là ẩn menu ở frontend; quyết định cuối cùng vẫn được enforcement tại API và retrieval layer.
>
> Frontend của dự án dùng TanStack Start và React; backend dùng FastAPI, SQLAlchemy, PostgreSQL với pgvector, cùng Redis/RQ cho background jobs. Phần tôi tập trung nhiều nhất không phải là gọi một LLM API, mà là các contract xung quanh nó: permission trước retrieval, evidence có vòng đời rõ ràng, citation được xác thực và các quyết định quan trọng đều có trace. Đây là một dự án engineering portfolio đang tiếp tục được đánh giá bằng các harness riêng cho chat, retrieval, Graph RAG và OCR. Cảm ơn bạn đã xem.

## 6. Claim an toàn cho portfolio

### Có thể nói

- “Hệ thống thực hiện patient-scope authorization trước khi retrieval.”
- “Citation không thuộc tập evidence đã retrieve sẽ bị chặn trước khi câu trả lời tới client.”
- “Document pipeline tạo pages, chunks, embeddings, BM25 vector và Graph entities/relations.”
- “Graph endpoint chỉ dùng nguồn active, patient-scoped và giữ document/chunk provenance.”
- “Audit logs chỉ dành cho Security/Admin; patient access denial được ghi audit.”
- “Dữ liệu demo là synthetic.”

### Không nên nói

- “Production-ready”, “đã triển khai tại bệnh viện” hoặc “đạt HIPAA”.
- “Không thể hallucinate” hoặc “zero PHI leakage” như một kết luận production.
- “OCR đạt X% accuracy” khi chưa có artifact benchmark CER/WER tương ứng.
- “Graph RAG đã cải thiện chất lượng X%” khi chưa có benchmark/ablation được phê duyệt.
- “Real-time token streaming trực tiếp từ LLM”; implementation hiện giữ output để validation trước khi phát.
- “Dùng dữ liệu bệnh nhân thật”.

## 7. Source evidence cho các nội dung trong video

| Nội dung demo | Source chính | Điều source chứng minh |
|---|---|---|
| Patient permission trước retrieval | `app/backend/src/hospital_ai/services/permissions.py:107-166` | Kiểm tra scope, phát hiện permission hết hạn, ghi audit và từ chối truy cập. |
| Safe streaming và citation validation | `app/backend/src/hospital_ai/api/routes/chat_stream.py:328-456` | Buffer output, chạy output guardrail, kiểm tra citation thuộc authorized evidence, chỉ emit cited evidence. |
| Trạng thái xử lý trên UI | `app/backend/src/hospital_ai/api/routes/chat_stream.py:218-222` | Các stage `retrieving`, `preparing_answer`, `validating_citations`. |
| Graph RAG theo patient | `app/backend/src/hospital_ai/api/routes/graph.py:116-181` | Permission check và lọc document/page/chunk active, nhất quán patient ID. |
| Graph provenance | `app/backend/src/hospital_ai/api/routes/graph.py:208-324` | Relation và reasoning step giữ source document/chunk. |
| OCR và document indexing | `app/backend/src/hospital_ai/services/ocr.py:43-105` | Native PDF text path và PaddleOCR fallback cho image-only page. |
| Background processing | `app/backend/src/hospital_ai/workers/jobs.py:19-172` | OCR, chunk, embedding, BM25, graph indexing, status, generation và source hash. |
| Audit role boundary | `app/backend/src/hospital_ai/api/routes/audit.py:16-35` | Chỉ Security/Admin được đọc audit logs. |
| Câu hỏi demo và UAT boundary | `app/backend/scripts/uat_product_api_check.py:232-333` | Patient-linked cited answer, denied access và Security audit scenario. |
| UI Patient Graph | `app/frontend/src/routes/_app.graph.patients.$patientId.tsx:23-158` | Fetch graph thật từ API, hiển thị entities, reasoning path và legend. |
| UI OCR queue | `app/frontend/src/routes/_app.documents.ocr-queue.tsx:16-46` | Hiển thị backlog, status và confidence. |

## 8. Checklist trước khi bấm Record

- [ ] Nhãn `Synthetic Data` đang hiển thị.
- [ ] Alice Synthetic có permission `Allowed` cho Cardiologist.
- [ ] Câu hỏi demo trả về ít nhất một citation đúng nguồn.
- [ ] Citation viewer mở được document/page.
- [ ] Patient Graph có relation và provenance, không chỉ có patient node.
- [ ] PDF dùng để upload không chứa dữ liệu thật.
- [ ] OCR worker/Redis đang chạy nếu quay live upload.
- [ ] Audit feed có ít nhất một `denied` event.
- [ ] Security Auditor đăng nhập và xem được audit logs.
- [ ] Không có token, secret, `.env` hoặc log nhạy cảm trong khung hình.
- [ ] Đã quay thử một lần và cắt các khoảng chờ dài.

