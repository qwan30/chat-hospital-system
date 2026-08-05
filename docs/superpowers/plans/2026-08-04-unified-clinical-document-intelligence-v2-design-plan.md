# Sửa Unified Clinical Document Intelligence V2

## Tóm tắt

Chỉ chỉnh [2026-08-04-unified-clinical-document-intelligence-v2-design.md](</D:/projects/chatbot-hospital-system/docs/superpowers/specs/2026-08-04-unified-clinical-document-intelligence-v2-design.md>). Biến V2 thành normative amendment có thể triển khai, giữ nguyên hướng kiến trúc hiện tại và đóng các blocker về state, schema, quyền, API, R2 và migration.

PR #87 tiếp tục đóng; không tạo branch, commit, push hoặc PR. Không sửa code hay hai file dirty `AGENTS.md` và `CLAUDE.md`.

## Thay đổi thiết kế

- Thay “candidate successor” bằng authority map: V1 tiếp tục quản lý roles, input formats, observability và deployment; V2 thay thế revision, generation, Graph RAG, R2 versioning, streaming/evidence và mở rộng benchmark.
- Bỏ toàn bộ `tenant_id` khỏi V2. Patient permission, existing roles và deployment boundary tiếp tục là ranh giới bảo mật.
- Tách ba trạng thái độc lập:
  - `approved_revision_set_id`: revision đã được duyệt.
  - `active_index_generation_id`: generation đang phục vụ retrieval/chat.
  - `document_draft_heads`: mutable draft aggregate với `lock_version`.
- Mỗi lần lưu trang tạo immutable `document_page_revision`; draft head thay đổi page selection. Submit đóng băng một `document_revision_set`. Approve tạo generation `building`; generation cũ chỉ chuyển `superseded` sau transaction kích hoạt generation mới thành công.
- Bổ sung `document_index_generations` với revision-set FK, trạng thái `building | active | failed | superseded`, stage results, hashes và timestamps. Re-index thất bại không thay đổi active pointer.
- Bổ sung `ocr_blocks`, `ocr_lines`, `ocr_spans`; lưu offsets, polygon, confidence, reading order và `alignment_status = aligned | partially_aligned | stale`. Text sửa thủ công không được tiếp tục dùng geometry cũ như bằng chứng chính xác.
- Tách Graph RAG thành patient-scoped `graph_entities`, `graph_mentions`, `graph_relation_assertions` và `graph_relation_evidence`. Canonical entity không chứa một nguồn duy nhất; provenance nằm ở mention/assertion evidence.
- Thêm object/upload lifecycle: `pending_upload → uploaded_unverified → quarantined | verified → finalized | rejected`. Chỉ object `finalized` mới được OCR.
- Enforce R2 bằng unique immutable keys, conditional PUT `If-None-Match: *`, HEAD verification, SHA-256, byte size, magic-byte MIME validation, malware/quarantine result và atomic database finalization.
- Làm rõ “raw OCR không bị hủy” áp dụng trong retention lifecycle; authorized hard-delete xóa source, revisions và derived generations nhưng giữ audit tombstone không chứa PHI.

## Quyền và public contracts

- Không thêm role `clinical_reviewer`. Định nghĩa capability grants trên các role hiện có:
  - `document_revision.view_raw`
  - `document_revision.edit`
  - `document_revision.reject`
  - `document_revision.approve`
  - `document_revision.restore`
  - `ocr_engine.override`
  - `superseded_evidence.read`
- Default grants:
  - Doctor: view/edit khi có patient permission.
  - Records staff: view/edit/reject/restore và limited superseded access.
  - Admin: reject/approve/restore/override/superseded access; không edit mặc định.
  - Nurse, pharmacist, lab staff: view theo patient permission; không full-text edit mặc định.
  - Security: audit metadata; không đọc PHI revision nếu thiếu patient permission.
- Production bắt buộc `editor_id != approver_id`. `ALLOW_SELF_APPROVAL_FOR_SYNTHETIC_DATA=true` chỉ có hiệu lực khi `demo_mode=true` và document được đánh dấu synthetic.
- Định nghĩa đầy đủ các API dưới `/api/v1`:
  - `POST /documents/upload-sessions`
  - `POST /documents/{document_id}/uploads/{upload_id}/finalize`
  - `GET /documents/{document_id}/revision-sets`
  - `GET /documents/{document_id}/revision-sets/{revision_set_id}`
  - `PATCH /documents/{document_id}/draft/pages/{page_number}`
  - `POST /documents/{document_id}/draft/submit`
  - `POST /documents/{document_id}/revision-sets/{revision_set_id}/approve`
  - `POST /documents/{document_id}/revision-sets/{revision_set_id}/reject`
  - `POST /documents/{document_id}/revision-sets/{revision_set_id}/restore`
  - `POST /documents/{document_id}/index-generations/{generation_id}/retry`
  - Filtered graph and timeline GET endpoints.
- Mọi write API yêu cầu `Idempotency-Key`; draft write thêm `If-Match`. Chuẩn hóa `201`, `202`, `403`, `409`, `422` và retry/audit behavior.
- SSE tiếp tục dùng event `token`, nhưng contract xác nhận đây là validated output chunk. Mỗi chunk có `sequence`; metadata có `validation_mode: sentence_buffered`. Quy định cố định event ordering, terminal `done`, interrupted persistence và không bao giờ gửi raw model token.

## Migration và kiểm thử

- Migration theo thứ tự: thêm schema → backfill machine revision v1 → tạo approved revision sets → gắn legacy chunks/graph vào legacy active generation → bật active-generation filters → mới bật editor và approval.
- Không đánh dấu dữ liệu thật là approved tự động; chỉ synthetic/demo records đáp ứng policy được auto-migrate.
- Giữ legacy read path cho đến khi backfill và parity checks thành công; rollback chỉ đổi active pointer, không xóa generation.
- Thêm acceptance scenarios:
  - Hai editor cùng sửa trả `409` cho stale `If-Match`.
  - Người sửa không thể tự approve trong production.
  - Re-index B thất bại nhưng generation A vẫn phục vụ.
  - Edited span chuyển geometry sang `stale`.
  - Một canonical entity có nhiều mentions và nguồn độc lập.
  - Mọi lexical/vector/graph path loại wrong-patient và superseded generation.
  - Upload trùng key, sai checksum/MIME hoặc chưa finalize không được OCR.
  - SSE chỉ phát validated chunks theo sequence và persist trạng thái interrupted đúng contract.
  - Migration giữ nguyên citation/retrieval parity cho legacy synthetic documents.
- Benchmark thresholds được ghi vào artifact versioned, đóng băng sau qualification và trước holdout. Checklist không còn tuyên bố “không có placeholder” khi threshold artifact chưa tồn tại.

## Giả định đã khóa

- Đây là spec-only revision; chưa triển khai database, API, frontend hoặc worker.
- V2 là amendment của V1, chưa hợp nhất thành V3 governing spec.
- Multi-tenancy nằm ngoài phạm vi.
- Capability grants dùng các role hiện có; không thêm role mới.
- PR #87 giữ trạng thái đóng và không có GitHub mutation trong phần việc này.
