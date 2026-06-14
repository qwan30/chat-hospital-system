# Coding Standards

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.0 · Owner: Tech Lead · Last Updated: 2026-06-14  
> Reference: `docs/00-overview/project-foundation.md` Sections 12–14

## 1. Python (Backend)

| Element | Convention | Example |
|---------|-----------|---------|
| Module | snake_case | `chat_service.py`, `hms_connector.py` |
| Class | PascalCase | `ChatService`, `LLMManager`, `OllamaLLM` |
| Function | snake_case | `get_current_user()`, `embed_many()` |
| Variable | snake_case | `patient_id`, `trace_id` |
| Constant | UPPER_SNAKE | `MAX_HISTORY_MESSAGES`, `SAFE_NO_EVIDENCE_ANSWER` |
| Private | `_prefix` | `_cache_key()`, `_build_payload()` |

## 2. TypeScript / React (Frontend)

| Element | Convention | Example |
|---------|-----------|---------|
| Component file | PascalCase | `DocumentsTable.tsx`, `PatientList.tsx` |
| Component | PascalCase | `DocumentsTable`, `ChatLayout` |
| Hook | camelCase, `use` prefix | `useAuth()`, `useDocuments()` |
| Interface | PascalCase | `DocumentRow`, `ChatThread` |
| Function | camelCase | `formatDate()`, `patientId` |
| Constant | UPPER_SNAKE | `STATUS_COLORS`, `DEFAULT_PROMPTS` |

## 3. Database

| Element | Convention | Example |
|---------|-----------|---------|
| Table | snake_case, plural | `document_chunks`, `chat_threads` |
| Column | snake_case | `patient_id`, `created_at` |
| PK | `id` (UUID) | |
| FK | `<entity>_id` | `patient_id`, `uploaded_by` |
| Timestamp | `created_at`, `updated_at`, `deleted_at` | |
| Constraint | `ck_<table>_<column>` | `ck_users_role` |

## 4. Code Limits

| Rule | Limit |
|------|-------|
| Function | <50 lines |
| File | <800 lines |
| Nesting | <4 levels |
| Parameters | <5 |
| Line length | 120 (Python) / 100 (TS) |

## 5. Backend Rules

```python
# ✅ Route delegates to service
@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, session: AsyncSession = Depends(get_session)):
    return await ChatService(session, settings).answer(...)

# ❌ Business logic in route handler
# ❌ Raw SQL — use SQLAlchemy ORM
# ❌ Blocking .result() / .wait() in async context
```

## 6. Frontend Rules

```tsx
// ✅ Typed props, component composition
interface DocumentsTableProps { documents: DocumentRow[] }
export function DocumentsTable({ documents }: DocumentsTableProps) { ... }

// ❌ Inline everything, no types, inline styles
```

## 7. Error Handling

- Backend: `AppError` hierarchy → `@app.exception_handler` → always include `trace_id`
- Frontend: try/catch around API calls → `sonner` toast for transient errors
- Never swallow exceptions silently
- Log full context (trace_id, user_id, patient_id)

## 8. Testing

| Language | Framework | Location | Naming |
|----------|-----------|----------|--------|
| Python | pytest + pytest-asyncio | `tests/` | `test_<what>_<expected>` |
| TypeScript | Vitest | `__tests__/` | `*.test.tsx` |
| E2E | Playwright | `e2e/` | `*.spec.ts` |

```python
# Python naming
async def test_chat_blocks_unauthorized_patient():
async def test_embedding_returns_1024_dim_vector():

# TypeScript naming
test('renders empty state when no documents exist', () => {})
```

## 9. Git Commits

```
feat(chat): add streaming response via SSE
fix(permissions): prevent scope bypass on expired tokens
docs(api): document chat-threads endpoints
test(rag): add citation validation test
refactor(llm): extract provider interface
```

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created from codebase patterns — Python, TS, DB, testing conventions |
