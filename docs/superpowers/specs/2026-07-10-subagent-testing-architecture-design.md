# Thiết kế Kiến trúc Sub-Agent Kiểm thử Toàn diện (Chat Hospital System)

Dự án này sử dụng một kiến trúc sub-agent nhiều lớp kết hợp phương pháp "Adversarial Review" (Santa Method) để đảm bảo độ chính xác tuyệt đối khi đối soát tài liệu và kiểm thử chất lượng hệ thống.

## Mục tiêu
1. **Rà soát sâu (Deep Audit):** Phát hiện mọi sai lệch giữa tài liệu (`docs/`) và mã nguồn (`app/`).
2. **Kiểm thử chi tiết (Granular Testing):** Tăng cường số lượng sub-agent và chia nhỏ phạm vi test.
3. **Đánh giá đối kháng (Adversarial Review):** Mỗi sub-agent thực thi (Maker) đều có một sub-agent độc lập đi kèm để kiểm tra chéo (Reviewer).
4. **Kiểm thử người dùng thật:** Sử dụng browser automation để đánh giá chất lượng cuối cùng (đặc biệt là Chat và Graph RAG).

---

## Giai đoạn 1: Knowledge & Consistency Deep Audit (Khớp thông tin Doc vs Code)
Giai đoạn này tập trung vào việc đọc, phân tích và so sánh từng dòng mô tả trong document với logic thực tế của code.

* **Cấu trúc Agent:** 
  * `Doc-Code Auditor Agent` (Maker): Đọc toàn bộ `docs/` và `app/`, so sánh kiến trúc, cấu trúc API, và test plan hiện tại.
  * `Logic Verifier Agent` (Reviewer): Kiểm tra lại những điểm mà Auditor báo cáo là "lệch". Nhiệm vụ của Reviewer là xác định xem: Sự lệch này là do Document cũ (Outdated), hay do Code sai so với thiết kế ban đầu (Bug).
* **Output:** Tạo ra file `Drift_Report_VI.md` (Bằng tiếng Việt).
* **Workflow Gate (Chặn chờ duyệt):** Hệ thống sẽ DỪNG LẠI sau khi tạo báo cáo. Người dùng (Human) sẽ đọc báo cáo, quyết định cái nào code đúng/doc sai hoặc ngược lại, trước khi cho phép hệ thống đi tiếp.

---

## Giai đoạn 2: Highly Parallel Domain Testing (Kiểm thử chéo bằng Cặp Agent)
Chia nhỏ các domain kiểm thử ra cho nhiều cặp Agent xử lý song song để tăng tốc độ và độ chính xác.

* **Cặp 1: Backend API & Auth**
  * `API Tester Agent`: Chạy pytest cho auth, permissions, dashboard.
  * `API Reviewer Agent`: Phân tích kết quả test, kiểm tra xem test coverage đã đủ chưa, có bỏ sót case bảo mật nào không.
* **Cặp 2: HMS Data Sync**
  * `Sync Tester Agent`: Kiểm tra luồng BFF, đồng bộ snapshot, xử lý event thay đổi từ HMS.
  * `Sync Reviewer Agent`: Kiểm tra lại logs và các data boundary (PHI compliance).
* **Cặp 3: Graph RAG & AI Engine**
  * `AI Evaluator Agent`: Test chuyên sâu vào Graph RAG, citation rate, hallucination, và cơ chế chặn quyền (Context Leakage).
  * `AI Metric Reviewer Agent`: Đối chiếu kết quả test với tiêu chuẩn chất lượng (Faithfulness ≥ 90%, Leakage = 0%). Đảm bảo Evaluator không "chấm điểm nương tay".
* **Cặp 4: Frontend UI Components**
  * `Frontend Tester Agent`: Chạy Bun, typecheck, component tests.
  * `Frontend Reviewer Agent`: Kiểm tra các file test xem có thực sự test UI logic hay chỉ là render suông.

---

## Giai đoạn 3: Real-User E2E & Browser Quality Assurance (Trải nghiệm thực tế)
Kiểm tra đầu cuối sau khi các chức năng cốt lõi đã pass.

* **Cặp 5: E2E Playwright Automation**
  * `Playwright Executor`: Chạy bộ 56 tests trong `e2e/`.
  * `Playwright Debugger (Reviewer)`: Nếu test tạch, tự động đọc trace/video và tìm nguyên nhân (UI đổi, hay logic lỗi).
* **Cặp 6: Human Simulation (Sử dụng lệnh `/browser`)**
  * `Browser Persona Agent`: Bật trình duyệt thật, đăng nhập, chat với hệ thống bằng các case phức tạp, đặc biệt là các ca bệnh cần truy vấn Graph RAG.
  * `Quality Assessor Agent (Reviewer)`: Đọc trực tiếp giao diện (thông qua screenshot/DOM) để đánh giá câu trả lời của AI trên màn hình có tự nhiên, chính xác và có hiển thị Citation rõ ràng cho bác sĩ hay không.

---

## Các bước triển khai tiếp theo
1. Ghi nhận bản thiết kế này (Done).
2. Tạo Implementation Plan.
3. Kích hoạt Giai đoạn 1 để bắt đầu tạo `Drift_Report_VI.md`.
