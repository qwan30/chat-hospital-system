# Screen List

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  
> Reference: `docs/screen-design/` for PNG references

## Master Catalog (25 screens)

| SCR | Name | Route | States |
|-----|------|-------|--------|
| SCR-001 | Login | `/login` | Default, error, loading |
| SCR-002 | MFA Verification | `/login/mfa` | Code input, error, redirect |
| SCR-003 | Dashboard Populated | `/dashboard` | Loaded stats + patients |
| SCR-005 | Dashboard Empty | `/dashboard` | Onboarding hero |
| SCR-007 | Patient Overview | `/patients/[id]` | EMR + AI summary + citations |
| SCR-008 | Patient List | `/patients` | Search, scoped, empty |
| SCR-009 | Medication Review | `/patients/[id]/meds` | Drug list + interaction check |
| SCR-010 | Patient Summary | `/patients/[id]/summary` | AI structured summary |
| SCR-011 | Chat Landing | `/chat/new` | Hero + prompt suggestions |
| SCR-012 | Chat Thread List | `/chat` | Thread list, empty |
| SCR-013 | Chat Workspace | `/chat/[id]` | Messages + composer + evidence |
| SCR-014 | Cited Answer | (in chat) | Streaming + inline citations |
| SCR-015 | Documents Dashboard | `/documents` | Table + storage donut |
| SCR-016 | Document Upload | `/documents/upload` | Dropzone + batch progress |
| SCR-017 | OCR Review | `/documents/[id]/review` | Low-confidence + retry + stepper |
| SCR-018 | Impact Metrics | `/metrics` | Charts: time, cost, rate |
| SCR-019 | Audit Logs | `/audit` | Filtered events + compliance |
| SCR-020 | Event Detail | (audit drawer) | Full audit event metadata |
| SCR-020b | Global Search | (Ctrl+K palette) | Patients + docs + threads |
| SCR-021 | Access Denied | `/patients/[id]/denied` | No-treatment panel |
| SCR-022 | Access Request | (modal overlay) | Justification form |
| SCR-025 | User Settings | `/settings` | Profile, preferences, health |
| SCR-027 | Environment Switcher | (topbar) | Sandbox/Training/Production |

## States Matrix

| Screen | Loading | Empty | Error | Populated |
|--------|---------|-------|-------|-----------|
| Dashboard | Skeleton cards | DashboardHero | ErrorState | Full metrics |
| Chat | Skeleton answer | PromptGrid | Connection error | Messages |
| Patient List | Skeleton rows | PatientsState | Permission error | Rows |
| Patient Detail | Skeleton cards | — | 403 Denied | Full overview |
| Documents | Skeleton rows | EmptyStateCard | — | Table + chart |
| Audit | Skeleton rows | — | Permission denied | Event rows |
| Metrics | Skeleton cards | — | — | Charts populated |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 25-screen catalog with states matrix, route + design references |
