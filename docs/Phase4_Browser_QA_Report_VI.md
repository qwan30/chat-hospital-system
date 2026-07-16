# Báo Cáo Phase 4: Browser QA & Real-User E2E

**Thời gian chạy:** 2026-07-10
**Môi trường:** Docker (Python 3.11-slim) - Bỏ qua hoàn toàn lỗi cú pháp `Mapped[str | None]` của Python 3.9 local.
**Công cụ:** Playwright E2E (`bun run test:e2e`) với 6 workers.

## 1. Tóm tắt Kết quả (Executive Summary)

Khác biệt hoàn toàn với Phase 3 (khi Backend bị chết do không khởi động được), ở Phase 4 này Backend **đã hoàn toàn "sống khỏe"** trong Docker. Do đó, các bài test E2E tương tác qua UI (như người dùng thật) đã phản ánh chính xác 100% tình trạng của Business Logic.

- **Tổng số Test:** 119
- **Passed:** 106
- **Failed:** 13
- **Tỷ lệ Pass:** ~89%

Hệ thống đã phục hồi đáng kể so với đánh giá ban đầu, các luồng Auth (Đăng nhập, Phân quyền) và Dashboard cơ bản đều hoạt động tốt. Tuy nhiên, luồng nghiệp vụ cốt lõi quan trọng nhất (Chat AI và Graph RAG) đang gặp vấn đề nghiêm trọng.

## 2. Các Lỗi Nghiệp Vụ Cốt Lõi (Business Logic Failures)

Tất cả 13 lỗi failed đều tập trung vào luồng tương tác với tính năng AI (Chat và Graph).

### 2.1. Lỗi Lifecycle của Chat Stream (Chat GPT-like Flow)
- `e2e/chat-gpt-flow.spec.ts`: Lỗi ở luồng chat cơ bản (gõ câu hỏi → gửi → xem câu trả lời kèm citation).
- `e2e/chat-gpt-flow.spec.ts`: Lỗi ở luồng chat với bệnh nhân (không load được hội thoại mẫu hoặc citation).
- `e2e/chat-general.spec.ts`: Khung soạn thảo (Composer) không tự động re-enable sau khi AI trả lời xong.
- `e2e/chat-patient.spec.ts`: Nút Send không bị block khi hệ thống đang xử lý tin nhắn, dễ dẫn đến spam request.

### 2.2. Lỗi Cơ Chế Gián Đoạn (Interruption & Resume/Retry)
Khi backend mô phỏng việc bị gián đoạn stream (`simulate=stream-fail`), Frontend hoàn toàn không hiển thị các cơ chế phục hồi như thiết kế:
- `e2e/graph-patient.spec.ts`: Lỗi không hiện banner "Response interrupted at".
- `e2e/graph-patient.spec.ts`: Không hiện 2 nút "Resume" và "Retry" cho bác sĩ ấn.
- `e2e/graph-patient.spec.ts`: Bấm Stop sau khi gián đoạn không giữ được lý do báo lỗi cũ.

### 2.3. Lỗi Điều Hướng & Tìm Kiếm Bệnh Nhân
- `e2e/business-flow.spec.ts`: Bài test "Patients list → search → navigate to detail" bị failed do không tìm thấy element sau khi search. Dẫn đến toàn bộ bài test `FULL BUSINESS FLOW END-TO-END` gãy.

## 3. Nhận Xét & Hành Động Tiếp Theo

Trải nghiệm Bác sĩ (Doctor UX) hiện tại:
1. Có thể đăng nhập và xem danh sách chung.
2. Khi bắt đầu dùng AI (Chat & Graph) để hỏi bệnh án, luồng tương tác rất mong manh: Nếu mạng chập chờn, họ không có nút Retry. Nếu Chat đang trả lời, khung gõ không khóa. 

**Đề xuất Hành động cho Phase Fix (Phase 5):**
1. **Frontend:** Cập nhật lại UI Component của luồng Chat (thêm state disabled cho nút Send, thêm Banner Interruption, nút Resume/Retry).
2. **Frontend:** Sửa lỗi logic điều hướng ở màn hình tìm kiếm Bệnh nhân.
3. **Backend/Cấu hình:** Không cần đụng đến `models.py` (chỉ cần đảm bảo dự án luôn chạy bằng Python 3.10+ hoặc Docker hiện tại là đã ổn định). Tập trung fix logic stream để trả về đúng format mã lỗi cho Frontend xử lý gián đoạn.
