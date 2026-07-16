# Phase 1: Deep Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thực hiện rà soát sâu (Deep Audit) toàn bộ tài liệu (`docs/`) so với mã nguồn (`app/`) và xuất ra báo cáo `Drift_Report_VI.md`.

**Architecture:** Sử dụng mô hình cặp Agent (Maker - Reviewer). Chia quá trình rà soát thành 3 domain chính: Testing, Architecture, và API. Mỗi domain sẽ do một Auditor rà soát và một Verifier kiểm chứng lại độ chính xác trước khi ghi vào báo cáo cuối.

**Tech Stack:** File reading, Markdown, Sub-agent Orchestration.

## Global Constraints

- Báo cáo đầu ra bắt buộc phải viết bằng tiếng Việt và lưu tại `docs/Drift_Report_VI.md`.
- MỌI task đều phải tuân thủ nghiêm ngặt nguyên tắc: 1 Agent làm (Maker), 1 Agent độc lập kiểm tra (Reviewer). Reviewer có quyền reject nếu Maker làm hời hợt.
- Tuyệt đối không thay đổi code hay document trong Phase 1. Chỉ đọc và báo cáo.

---

### Task 1: Khởi tạo Cấu trúc Báo cáo (Drift_Report_VI.md)

**Files:**
- Create: `docs/Drift_Report_VI.md`

**Interfaces:**
- Produces: File `docs/Drift_Report_VI.md` rỗng với các header có sẵn để các task sau điền vào.

- [ ] **Step 1: Tạo template báo cáo**

Sử dụng lệnh để tạo file:
```bash
cat << 'EOF' > docs/Drift_Report_VI.md
# Báo Cáo Lệch Pha Code & Document (Drift Report)

Báo cáo này liệt kê chi tiết các điểm sai lệch giữa tài liệu thiết kế và hiện trạng mã nguồn thực tế.

## 1. Lệch Pha về Testing (Test Plan vs Tests)
(Chưa có dữ liệu)

## 2. Lệch Pha về Architecture (Architecture Docs vs Code Structure)
(Chưa có dữ liệu)

## 3. Lệch Pha về API (API Docs vs Backend Endpoints)
(Chưa có dữ liệu)

## 4. Đánh giá Tổng quan & Đề xuất Cập nhật
(Chưa có dữ liệu)
EOF
```

- [ ] **Step 2: Reviewer xác nhận template**
Agent Reviewer kiểm tra file `docs/Drift_Report_VI.md` đã được tạo đúng cấu trúc hay chưa.

---

### Task 2: Audit Phần Testing (docs/09-testing)

**Files:**
- Modify: `docs/Drift_Report_VI.md`

**Interfaces:**
- Consumes: `docs/09-testing/test-plan.md`, `app/frontend/e2e/`, `app/backend/tests/`

- [ ] **Step 1: Khởi tạo Auditor Agent (Maker)**
Gọi sub-agent đọc `test-plan.md`, sau đó so sánh với danh sách các file trong `app/frontend/e2e` và `app/backend/tests/`. Auditor sẽ ghi nhận các điểm lệch pha (ví dụ: cấu trúc thư mục flows/ không tồn tại, RAG vs Graph RAG).

- [ ] **Step 2: Cập nhật Drift_Report_VI.md (Section 1)**
Auditor Agent thay thế dòng `(Chưa có dữ liệu)` trong mục 1 bằng danh sách các sai lệch chi tiết.

- [ ] **Step 3: Khởi tạo Verifier Agent (Reviewer)**
Gọi sub-agent thứ hai. Agent này có nhiệm vụ tự truy cập lại `test-plan.md` và codebase, đối chiếu với nội dung Auditor vừa viết vào `Drift_Report_VI.md`. Nếu Auditor bỏ sót (như chưa nhắc tới việc thiếu file RTM), Verifier sẽ đánh dấu fail và yêu cầu sửa.

---

### Task 3: Audit Phần Architecture (docs/04-architecture)

**Files:**
- Modify: `docs/Drift_Report_VI.md`

**Interfaces:**
- Consumes: `docs/04-architecture/`, `app/`

- [ ] **Step 1: Khởi tạo Auditor Agent (Maker)**
Auditor đọc các file kiến trúc chính (ví dụ `architecture.md`, sơ đồ luồng dữ liệu) và so sánh với cấu trúc thư mục thực tế của `app/frontend` và `app/backend`. 

- [ ] **Step 2: Cập nhật Drift_Report_VI.md (Section 2)**
Ghi chép các thành phần kiến trúc có trong doc nhưng chưa có trong code (hoặc ngược lại).

- [ ] **Step 3: Khởi tạo Verifier Agent (Reviewer)**
Verifier kiểm tra chéo lại kết quả của Auditor đối với phần Architecture, đảm bảo mọi kết luận "lệch" đều có bằng chứng (ví dụ file nào thiếu, folder nào dư).

---

### Task 4: Audit Phần API (docs/05-api)

**Files:**
- Modify: `docs/Drift_Report_VI.md`

**Interfaces:**
- Consumes: `docs/05-api/`, backend router code (VD: `app/backend/src/routers/` hoặc tương tự)

- [ ] **Step 1: Khởi tạo Auditor Agent (Maker)**
So sánh spec API trong docs với định nghĩa routes/endpoints thực tế của FastAPI trong `app/backend`. Tìm các endpoint mới được thêm vào code nhưng doc chưa có.

- [ ] **Step 2: Cập nhật Drift_Report_VI.md (Section 3)**
Cập nhật những API bị lệch vào Section 3 của báo cáo.

- [ ] **Step 3: Khởi tạo Verifier Agent (Reviewer)**
Verifier kiểm tra chéo, đảm bảo Auditor không bắt lỗi sai (ví dụ endpoint chỉ đổi tên variable).

---

### Task 5: Tổng hợp & Final Review

**Files:**
- Modify: `docs/Drift_Report_VI.md`

- [ ] **Step 1: Viết Tổng kết (Maker)**
Auditor Agent viết phần "4. Đánh giá Tổng quan & Đề xuất Cập nhật", tóm tắt lại mức độ nghiêm trọng của sự lệch pha và đề xuất action plan.

- [ ] **Step 2: Final Review (Reviewer)**
Verifier Agent đọc lại TOÀN BỘ `Drift_Report_VI.md`. Đảm bảo file được trình bày đẹp, đúng format Markdown, tiếng Việt chuẩn xác và logic chặt chẽ.

- [ ] **Step 3: Commit**
```bash
git add docs/Drift_Report_VI.md
git commit -m "docs: add Phase 1 Drift Report for Code vs Docs"
```
