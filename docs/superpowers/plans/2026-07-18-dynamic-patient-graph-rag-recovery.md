# Dynamic Patient Data & Graph RAG Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `ecc:subagent-driven-development` to implement task-by-task with spec-compliance and code-quality review after every task.

**Goal:** Chuyển các phần còn giá trị của branch umbrella cũ thành một chuỗi PR nhỏ, an toàn, kiểm thử được và release-ready trên `origin/main`.

**Architecture:** Không merge/cherry-pick toàn bộ `origin/feat/dynamic-patient-data-and-graph-rag` hoặc PR #27–#29. Mỗi PR mới bắt đầu từ `origin/main` mới nhất sau khi PR trước đã merge: baseline → thread authorization → BM25/schema → corpus governance → frontend truthfulness → certification.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic/PostgreSQL, pytest/Ruff, TanStack Start, React Query, Bun/Vitest/Playwright.

## Global Constraints

- Tạo isolated worktree; không dùng hoặc sửa checkout gốc đang ahead remote 85 commit và có dirty files.
- Không merge branch umbrella hoặc cherry-pick wholesale PR #27–#29.
- Không ingest public guideline/drug content vào patient retrieval; giữ trong quarantine tới khi provenance/license review hoàn tất.
- `Document.patient_id` và `DocumentChunk.patient_id` phải bắt buộc với patient RAG.
- Không được gửi chunk trái quyền, soft-deleted hoặc sai patient tới LLM.
- `/chat` và `/chat/stream` phải đồng nhất authorization, retrieval, citation, audit và persistence.
- Strict xfail, mocked browser test hoặc unavailable live backend không được tính là release evidence.
- Dùng `py -3.12` cho backend và Bun cho frontend.
- Mỗi task tuân thủ RED → GREEN → REFACTOR, commit riêng và review hai tầng.
- Chỉ sử dụng synthetic/de-identified data.

## Delivery order

1. PR-0: Khôi phục green baseline.
2. PR-1: Hoàn thiện chat-thread authorization.
3. PR-2: Sửa migration BM25/search-vector.
4. PR-3: Harden corpus/importer và loại public KB khỏi runtime.
5. PR-4: Frontend truthfulness và Graph UI.
6. PR-5: Release certification và đóng PR stale.

## Task 0: Restore a clean baseline

**Branch:** `codex/restore-green-baseline`

**Files:** `app/backend/tests/test_ci_workflow.py`, CI configuration only if a clean run proves it necessary.

- [ ] Tạo worktree từ SHA mới nhất của `origin/main`; xác nhận không có tracked changes.
- [ ] Sửa hai Ruff violations hiện có: import order và bỏ mode `"r"` không cần thiết.
- [ ] Chạy `py -3.12 -m ruff check src/ tests/` và `py -3.12 -m ruff format --check src/ tests/`; expected exit `0`.
- [ ] Chạy toàn bộ backend tests và contract verification; expected không có failed/strict-xfailed tests.
- [ ] Chạy `bun install --frozen-lockfile`, typecheck, lint, unit test và production build với `VITE_API_URL` hợp lệ.
- [ ] Commit `test: restore clean baseline gates`; chỉ merge khi toàn bộ CI xanh.

## Task 1: Centralize chat-thread message authorization

**Branch:** `codex/chat-thread-access-hardening` từ main sau PR-0.

**Primary files:** `services/chat_threads.py`, `services/chat.py`, `api/routes/chat_stream.py`; tests trong `test_chat_endpoint.py` và `test_chat_stream_endpoint.py`.

**Interface:**

```python
async def require_message_access(
    self,
    *,
    user: User,
    thread_id: UUID,
    request_patient_id: Optional[UUID],
    trace_id: str,
    ip_address: Optional[str],
) -> ChatThread
```

Behavior:

- Chỉ participant active với access `owner` hoặc `write` được gửi message.
- Thread phải tồn tại, chưa soft-delete và có status `active`.
- Patient-linked thread phải khớp request patient và user vẫn có patient-read permission.
- Missing/inaccessible thread trả `403`, không phân biệt để tránh UUID enumeration.
- Request-time failure xảy ra trước khi tạo `StreamingResponse`.
- Completion callback mở session mới và kiểm tra lại quyền trước khi persist.

Steps:

- [ ] Viết adversarial tests cho non-participant, soft-deleted participant, read-only participant, archived/deleted thread, patient mismatch và revoked patient permission.
- [ ] Chứng minh tests RED với `_get_conversation_history()` hiện tại.
- [ ] Implement `require_message_access()` bằng các predicate/audit helper sẵn có trong `ChatThreadService`.
- [ ] Đổi history loader thành nhận `ChatThread` đã authorize; không tự truy vấn participant lần hai.
- [ ] Dùng cùng helper trong sync chat, SSE request path và SSE completion persistence.
- [ ] Assert mọi denied case tạo audit record, không gọi embedding/LLM và không ghi `ChatMessage`/`AiQuery`.
- [ ] Chạy focused chat/thread/release-gate tests, rồi full backend suite.
- [ ] Commit `fix: enforce active chat thread message access`.

## Task 2: Restore the PostgreSQL BM25 schema contract

**Branch:** `codex/bm25-migration-repair`

**Migration:** `app/backend/alembic/versions/7f4c2a1d9e80_restore_document_chunk_search_vector.py`

**Contract:**

- `revision = "7f4c2a1d9e80"`
- `down_revision = "cfb28845ca63"`
- PostgreSQL column: `document_chunks.search_vector tsvector`
- Index: `ix_document_chunks_search_vector`, GIN
- Existing content được backfill bằng `to_tsvector('english', coalesce(content, ''))`.

Steps:

- [ ] Viết migration-chain test chứng minh `alembic upgrade head` hiện để mất `search_vector`.
- [ ] Thêm forward migration; không sửa migration đã merge `60e7683f03bd`.
- [ ] Làm upgrade idempotent đối với database có hoặc chưa có column/index.
- [ ] Downgrade trả schema về đúng trạng thái sau `cfb28845ca63`.
- [ ] Thêm PostgreSQL integration assertion cho column type, GIN index và truy vấn BM25 trên seeded chunk.
- [ ] Chạy migration từ database rỗng và upgrade từ previous head; cả hai phải xanh.
- [ ] Chạy retrieval SQL, hybrid-threshold và Graph RAG release-gate tests.
- [ ] Commit `fix: restore document chunk search vector migration`.

## Task 3: Govern and ingest the synthetic corpus safely

**Branch:** `codex/synthetic-corpus-governance`

**Key additions:**

- `services/ingestion_manifest.py`: immutable parsing/preflight/result types.
- `scripts/ingest_synthetic_dataset.py`: safe CLI orchestration.
- `scripts/quarantine_public_knowledge.py`: export/quarantine workflow.
- Migration `91b6d0e4a2c7_enforce_patient_document_scope.py`, down-revision `7f4c2a1d9e80`.

**CLI contract:**

```text
python scripts/ingest_synthetic_dataset.py --preflight-only --report <json>
python scripts/ingest_synthetic_dataset.py --apply --report <json>
python scripts/quarantine_public_knowledge.py --export-dir <path>
python scripts/quarantine_public_knowledge.py --export-dir <path> --apply
```

Rules:

- Preflight toàn bộ records trước lần ghi đầu tiên.
- Patient rows bắt buộc có valid patient/uploaded-by UUID, existing patient, supported MIME, existing source, SHA-256 và non-empty access tags.
- Global/public rows chỉ xuất hiện trong `quarantined_public_sources`; không tạo `Document`.
- `--apply` trả non-zero nếu có record failed/skipped do invalid state.
- Document identity dựa trên patient + normalized source identity; same hash skip, changed hash chạy generation-safe re-index.
- `process_document(..., *, access_tags: Sequence[str] = ())` gắn access tags ngay lúc tạo chunks, không patch sau indexing.
- Worker failure phải persist truthful `ocr_failed`/`index_failed` và xuất report; không swallow.

Steps:

- [ ] Viết preflight tests cho bad UUID, missing patient/source, unsupported MIME, hash mismatch, null patient và malformed JSONL.
- [ ] Viết integration tests chứng minh preflight failure tạo zero DB/file writes.
- [ ] Implement immutable manifest/result types và deterministic JSON report.
- [ ] Thêm `access_tags` keyword-only parameter vào worker; giữ default rỗng cho callers hiện có.
- [ ] Rewrite importer theo preflight-first, deterministic identity và truthful exit codes.
- [ ] Export mọi null-patient DB record cùng raw-file hash trước khi xóa derived rows; `--apply` chỉ chạy sau export thành công.
- [ ] Thêm forward migration enforce `documents.patient_id` và `document_chunks.patient_id` NOT NULL; migration fail closed nếu còn null rows.
- [ ] Loại `OR patient_id IS NULL` khỏi raw SQL và ORM retrieval predicates.
- [ ] Chọn `app/backend/data/` làm canonical corpus; tạo per-file SHA manifest rồi xóa 210 nested duplicates chỉ khi tất cả hash khớp.
- [ ] Di chuyển public guideline/drug metadata vào quarantine; giữ nguyên raw content và provenance.
- [ ] Chạy importer hai lần để chứng minh idempotency và chạy permission-leakage tests.
- [ ] Commit `fix: govern synthetic corpus ingestion`.

## Task 4: Make frontend behavior truthful and deterministic

**Branch:** `codex/frontend-truthfulness`

**In scope:** logout, GraphCanvas/reasoning path, evidence placeholders, static-page disclosure. Không import các backend, screenshot hoặc agent-state changes từ PR #27–#29.

Steps:

- [ ] Viết tests chứng minh sign-out hiện không gọi `AuthContext.logout`.
- [ ] Đổi `SessionProvider.signOut()` để xóa cả real-auth token/user và mock session trước navigation.
- [ ] Thêm unknown graph-node fallback style; không được drop node type lạ hoặc dùng `@ts-ignore`.
- [ ] Bỏ random 8% failure và simulated “streaming” khỏi patient graph; render server `reasoning_path` trực tiếp.
- [ ] Nếu citation metadata thiếu date/page field, omit UI field thay vì hiển thị placeholder như `Recent`.
- [ ] Giữ `/chat/general` redirect sang canonical `/chat`; thêm route regression test cấm hard-coded clinical answer.
- [ ] Gỡ Notifications, global Timeline và Metrics khỏi primary release navigation.
- [ ] Giữ các route cho portfolio/demo nhưng thêm banner cố định: “Static demonstration data — not connected to hospital systems”; disable actions giả như “Mark all as read”.
- [ ] Đánh dấu ba màn hình là `Demo` trong screen index và E2E expectations.
- [ ] Chạy Bun typecheck, lint, unit tests, build và focused Playwright.
- [ ] Commit `fix: make frontend data provenance explicit`.

## Task 5: Certify release and retire stale branches

**Branch:** `codex/rag-release-certification`

- [ ] Chạy full backend suite, Ruff check/format và API contract verifier.
- [ ] Chạy focused Graph RAG/chat gates; expected không failed hoặc strict-xfailed tests.
- [ ] Chạy `py -3.12 scripts/run_rag_eval.py`; expected 6/6 scenarios, citation/refusal rate `1.0`, unauthorized chunks `0`.
- [ ] Chạy migration chain trên PostgreSQL rỗng và upgraded database.
- [ ] Chạy Bun typecheck, lint, unit test và production build.
- [ ] Chạy Playwright với live seeded backend cho cross-user thread denial, revoked patient scope, SSE disconnect, general-chat redirect, unknown graph node và cited EvidenceRail.
- [ ] Ghi report phân biệt rõ local gates, GitHub CI và live-backend evidence.
- [ ] Yêu cầu toàn bộ GitHub checks xanh trước merge; mocked-only evidence không đủ.
- [ ] Đóng PR #27–#29 với link tới các successor PR tương ứng.
- [ ] Archive remote umbrella branch chỉ sau khi xác nhận mọi successor đã merge; không xóa local dirty branch.
- [ ] Commit `docs: certify graph rag recovery release`.

## Acceptance criteria

- Không user nào đọc hoặc ghi được thread ngoài active owner/write participation và patient permission hiện hành.
- PostgreSQL BM25 hoạt động sau full Alembic upgrade.
- Patient retrieval không bao giờ lấy null/global, deleted hoặc foreign-patient chunks.
- Importer preflight-first, idempotent, không swallow failure và không ingest public KB.
- Corpus chỉ còn một canonical copy với SHA manifest.
- Frontend không trình bày mock clinical/operational data như live production data.
- `/chat` và `/chat/stream` có cùng Graph RAG, citation, authorization, audit và persistence contracts.
- Tất cả local gates, CI và live-backend E2E đều xanh.

## Assumptions

- Các PR được triển khai tuần tự từ `origin/main`; không stack lên checkout local hiện tại.
- Public KB runtime integration nằm ngoài recovery này và cần plan riêng sau provenance/license review.
- Notifications/global Timeline/full Metrics APIs nằm ngoài scope; các màn hình được ẩn khỏi release navigation và gắn nhãn Demo.
- `gkg` hiện không có trong PATH; execution phải thử readiness lại, nhưng direct source và executable tests vẫn là source of truth.
