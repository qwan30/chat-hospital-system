# Plan: Figma-to-Code — React + shadcnUI Frontend Implementation

> **Source**: `master-figma-execution-plan.md` + `master-figma-task-breakdown.md`  
> **Target**: Convert all 25 Figma screens into a working TanStack Start + React + shadcnUI frontend
> **Generated**: 2026-06-10  
> **Complexity**: EXTRA LARGE (25 screens, ~90 components, design system, API integration)  
> **Status**: APPROVED — Ready for Execution  

---

## 1. Summary

The Figma design system is complete: 25 screens, ~90 components, and a full token set (colors, typography, spacing, effects). This plan covers converting every screen and component into production React code using TanStack Start App Router, shadcnUI, Tailwind CSS v4, Recharts, react-hook-form + zod, and the existing backend API. The plan respects the existing project patterns (API client, auth context, app shell layout) and the architectural rule that the frontend is a BFF consumer — no direct HMS DB access.

---

## 2. Current State Audit

| Layer | Status | Notes |
|-------|--------|-------|
| Figma design system | ✅ COMPLETE | 60+ color tokens, 13 typography presets, spacing/radius tokens |
| Figma base components | ✅ COMPLETE | 37 base components (buttons, inputs, chips, cards, tables, nav, overlays) |
| Figma domain components | ✅ COMPLETE | ~53 domain components (app shell, patient, chat, evidence, docs, audit, auth, viz, empty) |
| Figma screens | ✅ COMPLETE | 25 screens across 10 modules |
| Backend API | ✅ EXISTS | 14 route modules (auth, patients, chat, documents, audit, etc.) |
| Old frontend source | ❌ DELETED | Git history preserves patterns; `node_modules` still present with deps |
| shadcnUI components | Partial | Old `ui/` had: badge, button, card, input, label, table. Need to re-init. |
| Tailwind CSS v4 | ✅ Installed | Config needs restoration |
| Design token → code | ❌ NOT STARTED | Need `tailwind.config.ts` theme mapping |

---

## 3. Tech Stack (Inherited from old frontend)

| Concern | Library | Purpose |
|---------|---------|---------|
| Framework | TanStack Start (App Router) | Routing, SSR, layouts |
| UI primitives | shadcnUI + Radix UI | Accessible, composable components |
| Styling | Tailwind CSS v4 | Utility-first, design-token mapping |
| Icons | Lucide React | 1,000+ consistent icons |
| Forms | react-hook-form + @hookform/resolvers + zod | Type-safe, performant forms |
| Charts | Recharts | Line, bar, area, donut charts |
| Tables | @tanstack/react-table | Sortable, filterable data tables |
| Animation | Motion (prev. Framer Motion) | Micro-interactions, page transitions |
| HTTP | fetch + custom api-client | Centralized auth header injection |
| Testing | Vitest + React Testing Library + jsdom | Unit + component tests |
| Auth | AuthContext (React Context) | Token management, user state |
| Linting | ESLint + eslint-config-next | Code quality |

---

## 4. Design Token → Code Mapping

### 4.1 Color Tokens → Tailwind CSS Variables

```css
/* globals.css — Design Token Foundation */
:root {
  /* Brand/Primary */
  --color-primary-50: #F5F9FF;
  --color-primary-100: #EAF2FF;
  --color-primary-300: #8BB8FF;
  --color-primary-500: #2F7AF7;
  --color-primary-600: #0B5CDF;
  --color-primary-700: #004EC2;

  /* Backgrounds & Surfaces */
  --color-bg-app: #F7FAFF;
  --color-bg-page: #FFFFFF;
  --color-bg-surface: #FFFFFF;
  --color-bg-surface-tint: #F9FBFF;
  --color-bg-sidebar: #FAFCFF;
  --color-bg-overlay: rgba(15, 23, 42, 0.52);

  /* Borders */
  --color-border-subtle: #EEF3FB;
  --color-border-default: #DCE6F7;
  --color-border-strong: #BFD0EE;
  --color-border-focus: #2F7AF7;

  /* Typography Colors */
  --color-text-strong: #081A48;
  --color-text-default: #24365F;
  --color-text-muted: #5B6B92;
  --color-text-subtle: #8A98B8;
  --color-text-inverse: #FFFFFF;
  --color-text-link: #0B5CDF;

  /* Semantic Colors */
  --color-success-50: #F2FBF6;
  --color-success-100: #E8F8EF;
  --color-success-600: #12A763;
  --color-success-700: #087443;

  --color-danger-100: #FFF1F1;
  --color-danger-600: #EF4444;
  --color-danger-700: #B42318;

  --color-warning-100: #FFF6E5;
  --color-warning-500: #F59E0B;
  --color-warning-700: #B54708;

  --color-purple-100: #F1E9FF;
  --color-purple-600: #7C3AED;

  --color-cyan-100: #E6FAFC;
  --color-cyan-600: #0EA5B7;

  /* Chart Colors */
  --color-chart-blue: #1265F0;
  --color-chart-green: #18A957;
  --color-chart-orange: #FF6B00;
  --color-chart-purple: #7C3AED;
  --color-chart-grid: #E7EDF8;
  --color-chart-axis: #6B7898;

  /* Shadows */
  --shadow-card: 0 8px 24px rgba(20, 38, 80, 0.08);
  --shadow-modal: 0 18px 50px rgba(20, 38, 80, 0.18);
  --shadow-popover: 0 12px 34px rgba(20, 38, 80, 0.16);
  --effect-focus-ring: 0 0 0 3px rgba(11, 92, 223, 0.12);

  /* Radii */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-3xl: 24px;
  --radius-full: 9999px;
}
```

### 4.2 Typography → Tailwind Classes Mapping

| Figma Preset | Tailwind Classes | Size / Line-height | Weight | Usage |
|---|---|---|---|---|
| Display | `text-[34px] leading-[42px]` | 34px / 42px | Bold (700) | Auth marketing headline, empty hero title |
| H1 | `text-[28px] leading-[36px]` | 28px / 36px | Bold (700) | Page title |
| H2 | `text-[22px] leading-[30px]` | 22px / 30px | Bold (700) | Modal title, large section |
| H3 | `text-[18px] leading-[26px]` | 18px / 26px | Bold (700) | Card title, chat thread title |
| H4 | `text-[16px] leading-[24px]` | 16px / 24px | Bold (700) | Section title inside card |
| Metric | `text-[28px] leading-[34px]` | 28px / 34px | Bold (700) | KPI number |
| Body | `text-[14px] leading-[22px]` | 14px / 22px | Regular (400) | Paragraphs, clinical answer |
| BodyMedium | `text-[14px] leading-[22px]` | 14px / 22px | Medium (500) | Form values, row labels |
| BodyStrong | `text-[14px] leading-[22px]` | 14px / 22px | Semi Bold (600) | Label, table cell title |
| Caption | `text-[12px] leading-[16px]` | 12px / 16px | Regular (400) | Metadata, helper |
| CaptionStrong | `text-[12px] leading-[16px]` | 12px / 16px | Semi Bold (600) | Badge text, table header |
| Micro | `text-[11px] leading-[14px]` | 11px / 14px | Medium (500) | Small chips, page/chunk metadata |
| Button | `text-[14px] leading-[20px]` | 14px / 20px | Semi Bold (600) | Button labels |

### 4.3 Layout Geometry & Layering (z-index)

#### 4.3.1 Standard App Shell Layout (1448 × 1086)
- **Viewport**: 1448 × 1086
- **Sidebar**: X=0, Y=0, Width=244px, Height=1086px
- **Topbar**: X=244px, Y=0, Width=1204px, Height=84px
- **Content Area**: X=244px, Y=84px, Width=1204px, Height=1002px
- **Content Padding**: 24px (all sides)
- **Default Grid Gap**: 16px
- **Footer Disclaimer**: Y=1050px, aligned center within Content Area

#### 4.3.2 Wide App Shell Layout (1672 × 941)
- **Viewport**: 1672 × 941
- **Sidebar**: X=0, Y=0, Width=288px, Height=941px
- **Topbar**: X=288px, Y=0, Width=1384px, Height=84px
- **Content Area**: X=288px, Y=84px, Width=1384px, Height=857px
- **Content Padding**: Horizontal=28px, Vertical=24px
- **Default Grid Gap**: 20px
- **Footer Disclaimer**: Y=910px, aligned center within Content Area

#### 4.3.3 Z-Index Layer Scale
```yaml
z-base: 0
z-sidebar: 10
z-topbar: 20
z-rail: 30
z-dropdown: 200
z-drawer: 250
z-backdrop: 500
z-modal: 600
z-toast: 700
```

---

## 5. Patterns to Mirror

These patterns were extracted from the old frontend code (preserved in git history):

| Category | Source | Pattern |
|---|---|---|
| **Naming** | `app/frontend/src/components/ui/button.tsx` | shadcnUI convention: `components/ui/{name}.tsx`, default export + `cva` variants |
| **Naming** | `app/frontend/src/components/chat/ChatComposer.tsx` | Domain components: `components/{domain}/{Component}.tsx`, named exports |
| **Error handling** | `app/frontend/src/lib/api-client.ts` | Centralized `ApiError` class with `status`/`code`/`message`; `apiFetch<T>` wrapper |
| **Auth** | `app/frontend/src/lib/auth-context.tsx` | React Context with `useAuth()` hook returning `{user, token, isLoading, isAuthenticated, logout}` |
| **API calls** | `app/frontend/src/lib/chat-assistant/api.ts` | Module-level API functions: `fetchChatThreads(opts)`, `sendChatMessage(opts, body)` |
| **Layout** | `app/frontend/src/app/(app)/layout.tsx` | Route group `(app)` with AppShellLayout: sidebar + main content + command palette |
| **Tests** | `app/frontend/__tests__/` | Vitest + React Testing Library, `__tests__/` colocated or at root, `.test.tsx` suffix |
| **State** | `app/frontend/src/lib/chat-assistant/stream-client.ts` | Custom hooks for SSE streaming, `useStreamingChat` pattern |

---

## 6. File Structure Target

```
app/frontend/
├── package.json
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── components.json              # shadcnUI config
├── eslint.config.mjs
├── vitest.config.ts
├── src/
│   ├── app/
│   │   ├── globals.css          # Design tokens + Tailwind directives
│   │   ├── layout.tsx           # Root layout (AuthProvider)
│   │   ├── page.tsx             # Redirect to /dashboard
│   │   ├── icon.svg
│   │   ├── login/
│   │   │   ├── page.tsx         # SCR-001: SSO Login
│   │   │   └── mfa/
│   │   │       └── page.tsx     # SCR-002: MFA Verification
│   │   └── (app)/               # Authenticated route group
│   │       ├── layout.tsx       # AppShellLayout (sidebar + header + content + cmd palette)
│   │       ├── dashboard/
│   │       │   └── page.tsx     # SCR-003/004/005: Dashboard (populated/empty/toast)
│   │       ├── patients/
│   │       │   ├── page.tsx     # SCR-006/009: Patient list / empty
│   │       │   └── [id]/
│   │       │       ├── page.tsx           # SCR-007: Patient overview
│   │       │       ├── summary/
│   │       │       │   └── page.tsx       # SCR-010: AI summary stream
│   │       │       ├── meds/
│   │       │       │   └── page.tsx       # SCR-008: Medication review
│   │       │       └── denied/
│   │       │           └── page.tsx       # SCR-021: Access denied
│   │       ├── chat/
│   │       │   ├── page.tsx     # SCR-013: Chat landing
│   │       │   ├── new/
│   │       │   │   └── page.tsx # SCR-011: New patient context thread
│   │       │   └── [id]/
│   │       │       └── page.tsx # SCR-012/014: Chat thread (cited answer / safe refusal)
│   │       ├── documents/
│   │       │   ├── page.tsx     # SCR-015: OCR indexing dashboard
│   │       │   ├── upload/
│   │       │   │   └── page.tsx # SCR-017: Batch upload (modal route)
│   │       │   └── [id]/
│   │       │       ├── review/
│   │       │       │   └── page.tsx  # SCR-016: OCR review
│   │       │       └── page.tsx      # SCR-018: Document pages preview
│   │       ├── audit/
│   │       │   └── page.tsx     # SCR-023: Audit events log
│   │       ├── metrics/
│   │       │   └── page.tsx     # SCR-024: Impact quality dashboard
│   │       └── settings/
│   │           └── page.tsx     # SCR-025: Profile & system preferences
│   ├── components/
│   │   ├── ui/                  # shadcnUI base (re-initialized via `shadcn add`)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── card.tsx
│   │   │   ├── table.tsx
│   │   │   ├── label.tsx
│   │   │   ├── select.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── dialog.tsx        # Modal
│   │   │   ├── sheet.tsx         # Drawer
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── toast.tsx + use-toast.ts
│   │   │   ├── tooltip.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── checkbox.tsx
│   │   │   ├── radio-group.tsx
│   │   │   ├── switch.tsx        # Toggle
│   │   │   ├── textarea.tsx
│   │   │   ├── input-otp.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   ├── command.tsx       # Command palette
│   │   │   ├── popover.tsx
│   │   │   └── progress.tsx
│   │   ├── app-shell/
│   │   │   ├── Topbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── RightRail.tsx
│   │   │   └── CommandPalette.tsx     # SCR-020
│   │   ├── auth/
│   │   │   ├── SplitLayout.tsx
│   │   │   ├── MarketingFeatureList.tsx
│   │   │   ├── LoginCard.tsx
│   │   │   ├── SSOButton.tsx
│   │   │   ├── EmailPasswordForm.tsx
│   │   │   ├── SecurityAssuranceBox.tsx
│   │   │   ├── MFACard.tsx
│   │   │   ├── OTPInputGroup.tsx
│   │   │   ├── CountdownResend.tsx
│   │   │   └── AuthTrustStrip.tsx
│   │   ├── patient/
│   │   │   ├── DetailHeader.tsx
│   │   │   ├── MetadataGrid.tsx
│   │   │   ├── SummaryStrip.tsx
│   │   │   ├── ContextChip.tsx
│   │   │   ├── AISummaryCard.tsx
│   │   │   ├── ClinicalSection.tsx
│   │   │   ├── MiniLabStrip.tsx
│   │   │   ├── MedicationList.tsx
│   │   │   ├── AllergyAlertsCard.tsx
│   │   │   ├── EncounterTimeline.tsx
│   │   │   └── RecentPatientsCard.tsx
│   │   ├── chat/
│   │   │   ├── LandingHero.tsx
│   │   │   ├── SuggestionCard.tsx
│   │   │   ├── PromptGrid.tsx
│   │   │   ├── Composer.tsx
│   │   │   ├── UserBubble.tsx
│   │   │   ├── AssistantCard.tsx
│   │   │   ├── StreamingAnswer.tsx
│   │   │   ├── SafeRefusalCard.tsx
│   │   │   ├── GeneralKnowledgeToggle.tsx
│   │   │   └── HowItWorksRail.tsx
│   │   ├── evidence/
│   │   │   ├── EvidenceRail.tsx
│   │   │   ├── CitationCard.tsx
│   │   │   ├── CitationLoading.tsx
│   │   │   ├── InlineCitation.tsx
│   │   │   ├── DocumentViewerModal.tsx  # SCR-019
│   │   │   ├── CitationDetails.tsx
│   │   │   ├── NoEvidenceRail.tsx
│   │   │   ├── RetrievalStepper.tsx
│   │   │   └── VerificationChecklist.tsx
│   │   ├── document/
│   │   │   ├── UploadDropzone.tsx
│   │   │   ├── UploadDropzoneCompact.tsx
│   │   │   ├── DocumentsTable.tsx
│   │   │   ├── BatchUploadModal.tsx
│   │   │   ├── UploadFileTable.tsx
│   │   │   ├── OCRPipelineStepper.tsx
│   │   │   ├── OCRReviewPage.tsx
│   │   │   ├── LowConfidenceBanner.tsx
│   │   │   ├── ScannedPagePane.tsx
│   │   │   ├── ExtractedTextPane.tsx
│   │   │   ├── ProcessingTimeline.tsx
│   │   │   ├── FailureReasonsCard.tsx
│   │   │   ├── SemanticSearchPanel.tsx
│   │   │   ├── MatchingChunkCard.tsx
│   │   │   └── StorageUsageDonut.tsx
│   │   ├── access/
│   │   │   ├── DeniedPanel.tsx
│   │   │   ├── RequestDetailsGrid.tsx
│   │   │   ├── NextActionsRail.tsx
│   │   │   ├── RequestModal.tsx
│   │   │   ├── ExplainerTimeline.tsx
│   │   │   ├── PurposeRadioCard.tsx
│   │   │   └── JustificationTextarea.tsx
│   │   ├── audit/
│   │   │   ├── MetricCard.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── EventsTable.tsx
│   │   │   ├── EventDrawer.tsx
│   │   │   └── ComplianceCard.tsx
│   │   ├── viz/
│   │   │   ├── TrendLineChart.tsx
│   │   │   ├── BarVolumeChart.tsx
│   │   │   ├── QualitySafetyChart.tsx
│   │   │   ├── WorkflowImpactTable.tsx
│   │   │   ├── UserFeedbackCard.tsx
│   │   │   └── StorageDonutChart.tsx
│   │   └── empty/
│   │       ├── DashboardHero.tsx
│   │       ├── PatientsState.tsx
│   │       ├── TableRow.tsx
│   │       ├── SkeletonMetricCard.tsx
│   │       ├── SkeletonThreadCard.tsx
│   │       └── SkeletonCitationCard.tsx
│   ├── lib/
│   │   ├── utils.ts               # cn() helper (clsx + tailwind-merge)
│   │   ├── api-client.ts          # Centralized fetch wrapper + ApiError
│   │   ├── auth-context.tsx        # AuthProvider + useAuth hook
│   │   ├── constants.ts           # Global UI constants (user, env, nav items)
│   │   ├── api/
│   │   │   ├── auth.ts            # login, mfa verify
│   │   │   ├── dashboard.ts       # dashboard summary
│   │   │   ├── patients.ts        # patient search, overview, summary
│   │   │   ├── chat.ts            # threads, messages, stream
│   │   │   ├── documents.ts       # document list, upload, OCR
│   │   │   ├── audit.ts           # audit events
│   │   │   ├── access.ts          # access requests
│   │   │   ├── metrics.ts         # impact metrics
│   │   │   ├── search.ts          # global search
│   │   │   └── settings.ts        # user preferences
│   │   └── stream/
│   │       └── stream-client.ts   # SSE/streaming chat client
│   └── hooks/
│       ├── use-debounce.ts
│       └── use-media-query.ts
└── __tests__/
    ├── setup.ts
    ├── components/                 # Component tests mirror src/components/
    └── pages/                      # Page integration tests
```

---

## 7. Implementation Phases

### PHASE 0: Project Scaffold & Foundation (Est. 3 hours)

**Goal**: Re-establish the TanStack Start project with all dependencies, shadcnUI init, and design token setup.

| # | Task | Est. | Validate |
|---|------|------|----------|
| 0.1 | Recreate `package.json` with all deps from git history | 15m | `npm install` succeeds |
| 0.2 | Recreate `next.config.ts`, `tsconfig.json`, `postcss.config.mjs` | 15m | `next dev` starts |
| 0.3 | Create `components.json` (shadcnUI config) with project colors | 10m | `shadcn add button` works |
| 0.4 | Init all shadcnUI components (button, input, badge, card, table, label, select, tabs, separator, dialog, sheet, dropdown-menu, toast, tooltip, skeleton, checkbox, radio-group, switch, textarea, input-otp, breadcrumb, command, popover, progress) | 30m | All components in `components/ui/` |
| 0.5 | Create `globals.css` with design-token CSS custom properties (Section 4) + Tailwind directives | 20m | Colors render in dev |
| 0.6 | Create `tailwind.config.ts` with design token → Tailwind theme mapping (colors, fontSize, borderRadius, boxShadow) | 20m | IntelliSense shows custom tokens |
| 0.7 | Create `src/lib/utils.ts` with `cn()` helper | 5m | Import works |
| 0.8 | Create `src/lib/api-client.ts` with `ApiError` + `apiFetch<T>` (mirror old pattern) | 20m | Compiles |
| 0.9 | Create `src/lib/auth-context.tsx` with `AuthProvider` + `useAuth` | 15m | Context provides user/token |
| 0.10 | Create `src/lib/constants.ts` with global UI constants | 10m | Import works |
| 0.11 | Create `src/app/layout.tsx` (root, wraps AuthProvider) and `src/app/page.tsx` (redirect to /dashboard) | 10m | App renders |
| 0.12 | `rtk next build` — verify green build | 10m | Build succeeds |

**Phase 0 Exit Gate**: `next build` passes, `next dev` serves a blank app, all shadcnUI components available.

---

### PHASE 1: App Shell (Est. 4 hours)

**Goal**: Build the persistent layout that wraps all authenticated screens.

| # | Task | Est. | Validate |
|---|------|------|----------|
| 1.1 | Create `Topbar.tsx` — logo, search input, environment pill, user avatar (64px height) | 45m | Renders at correct height |
| 1.2 | Create `Sidebar.tsx` — 8 nav items, recent items section, permission card, footer (256px width) | 45m | Active state, collapsed state |
| 1.3 | Create `Footer.tsx` — safety disclaimer text | 10m | Renders in content area |
| 1.4 | Create `RightRail.tsx` — stacked card container (300-340px) | 15m | Flexible width |
| 1.5 | Create `CommandPalette.tsx` — ⌘K overlay, search input, results sections (patients/docs/threads/commands) | 45m | Opens on Ctrl+K, search debounce, keyboard nav |
| 1.6 | Create `src/app/(app)/layout.tsx` — AppShellLayout composing Topbar + Sidebar + Content + CommandPalette | 30m | All nav links navigate |
| 1.7 | Create `src/app/login/page.tsx` — stub (full implementation in Phase 2) | 10m | Redirects unauthenticated users |
| 1.8 | Test: sidebar nav, command palette, responsive collapse | 20m | Manual verification in dev |

**Phase 1 Exit Gate**: Authenticated shell renders, sidebar navigates, command palette opens/closes.

---

### PHASE 2: Auth Module (Est. 3 hours)

**Goal**: Login and MFA screens with form validation.

| # | Task | Est. | API |
|---|------|------|-----|
| 2.1 | Create API module: `lib/api/auth.ts` — `login()`, `verifyMfa()` | 20m | `POST /api/v1/auth/login`, `/auth/mfa/verify` |
| 2.2 | Create `Auth/SplitLayout.tsx` — 45/55 split with marketing pane + form pane | 30m | |
| 2.3 | Create `Auth/MarketingFeatureList.tsx` — 4 feature bullets with icons | 15m | |
| 2.4 | Create `Auth/LoginCard.tsx` — SSO button + divider + email/password form (react-hook-form + zod) | 45m | |
| 2.5 | Create `Auth/SSOButton.tsx` — full-width hospital SSO button | 15m | |
| 2.6 | Create `Auth/EmailPasswordForm.tsx` — email + password inputs | 20m | |
| 2.7 | Create `Auth/SecurityAssuranceBox.tsx` — 3 trust chips | 15m | |
| 2.8 | Create `Auth/MFACard.tsx` — lock icon + OTP inputs + countdown | 30m | |
| 2.9 | Create `Auth/OTPInputGroup.tsx` — 6 digit boxes (shadcn input-otp) | 15m | |
| 2.10 | Create `Auth/CountdownResend.tsx` — timer + resend link | 15m | |
| 2.11 | Create `Auth/AuthTrustStrip.tsx` — 3-column trust banner | 15m | |
| 2.12 | Build `login/page.tsx` (SCR-001) — compose all auth components | 20m | |
| 2.13 | Build `login/mfa/page.tsx` (SCR-002) — compose MFA components | 20m | |
| 2.14 | Test: login flow, form validation, error states, MFA redirect | 15m | Test with Vitest |

**Phase 2 Exit Gate**: Login form validates, submits to API, MFA screen renders.

---

### PHASE 3: Dashboard Module (Est. 4 hours)

**Goal**: Populated dashboard, empty state, toast overlay, user menu.

| # | Task | Est. | API |
|---|------|------|-----|
| 3.1 | Create API module: `lib/api/dashboard.ts` | 15m | `GET /api/v1/dashboard/summary` |
| 3.2 | Create `Empty/DashboardHero.tsx` — illustration + "No data yet" + CTAs | 20m | |
| 3.3 | Create `Empty/SkeletonMetricCard.tsx` — pulsing KPI placeholder | 10m | |
| 3.4 | Create `Empty/SkeletonThreadCard.tsx` — pulsing thread placeholder | 10m | |
| 3.5 | Create `viz/TrendLineChart.tsx` — line chart with before/after comparison (Recharts) | 30m | |
| 3.6 | Create `viz/BarVolumeChart.tsx` — bar chart for volumes (Recharts) | 20m | |
| 3.7 | Build `dashboard/page.tsx` — SCR-005 (empty state, no data) | 30m | |
| 3.8 | Build SCR-003 state — populated dashboard: 4 KPI cards, composer, recent patients table (5 rows), charts ×2, info cards ×3 | 1h | |
| 3.9 | Build SCR-004 state — user dropdown menu (profile, preferences, switch role/workspace, help, logout) | 30m | |
| 3.10 | Build toast stack overlay — 2 success toasts positioned bottom-right | 15m | |
| 3.11 | Test: dashboard components, empty→populated transition, user menu | 15m | Vitest |

**Phase 3 Exit Gate**: Dashboard renders both empty and populated states, KPI cards show real data, charts render.

---

### PHASE 4: Patients Module (Est. 8 hours)

**Goal**: Patient list, patient overview with AI summary, medication review, AI summary streaming, access denied. (6 screens — largest module)

| # | Task | Est. | API |
|---|------|------|-----|
| 4.1 | Create API module: `lib/api/patients.ts` | 15m | Search, overview, summary, med-review |
| 4.2 | Create `Patient/DetailHeader.tsx` — avatar, name, MRN, status chips, bookmark, kebab menu | 45m | |
| 4.3 | Create `Patient/MetadataGrid.tsx` — 2×4 grid: DOB, Sex, Phone, MRN, Blood Type, Dept, Attending, Status, Admitted, Room | 30m | |
| 4.4 | Create `Patient/ContextChip.tsx` — compact patient name + MRN + permission | 15m | |
| 4.5 | Create `Patient/SummaryStrip.tsx` — compact for modals | 15m | |
| 4.6 | Create `Patient/AISummaryCard.tsx` — sections with citations, confidence footer | 45m | |
| 4.7 | Create `Patient/ClinicalSection.tsx` — section row: icon + title + content + inline citations | 20m | |
| 4.8 | Create `Patient/MiniLabStrip.tsx` — horizontal lab values with trend/status | 25m | |
| 4.9 | Create `Patient/MedicationList.tsx` — medication rows with dosage, frequency, citation | 25m | |
| 4.10 | Create `Patient/AllergyAlertsCard.tsx` — allergy list with severity icons | 20m | |
| 4.11 | Create `Patient/EncounterTimeline.tsx` — vertical timeline with status chips | 25m | |
| 4.12 | Create `Patient/RecentPatientsCard.tsx` — sidebar card with avatar + name list | 15m | |
| 4.13 | Create `Empty/PatientsState.tsx` — illustration + "No patients found" + CTAs | 15m | |
| 4.14 | Build `patients/page.tsx` — SCR-009 (empty) and SCR-006 (populated: search, filters, table ×8 rows, right rail) | 1h | |
| 4.15 | Build `patients/[id]/page.tsx` — SCR-007 (overview: header, metadata, tabs, AI summary, sections, citations, timeline) | 1.5h | |
| 4.16 | Build `patients/[id]/summary/page.tsx` — SCR-010 (context chip, user bubble, streaming answer, retrieval stepper, citation cards) | 45m | |
| 4.17 | Build `patients/[id]/meds/page.tsx` — SCR-008 (medication review with cited answer, allergy warnings, recommendation) | 45m | |
| 4.18 | Build `patients/[id]/denied/page.tsx` — SCR-021 (denied panel, request details, next actions rail) | 45m | |
| 4.19 | Test: patient list/search, overview render, streaming skeleton, access denied state | 30m | Vitest |

**Phase 4 Exit Gate**: All 6 patient screens render, patient data flows from API, streaming UI works.

---

### PHASE 5: Chat Module (Est. 5 hours)

**Goal**: Chat landing, new thread, cited answer, safe refusal, streaming.

| # | Task | Est. | API |
|---|------|------|-----|
| 5.1 | Create API module: `lib/api/chat.ts` + `lib/stream/stream-client.ts` | 30m | Threads, messages, stream SSE |
| 5.2 | Create `Chat/LandingHero.tsx` — bot illustration + greeting + suggestion cards | 30m | |
| 5.3 | Create `Chat/SuggestionCard.tsx` — action card with icon, title, subtitle | 15m | |
| 5.4 | Create `Chat/PromptGrid.tsx` — 2×3 grid of suggested prompts | 20m | |
| 5.5 | Create `Chat/Composer.tsx` — input bar with action buttons, streaming toggle | 30m | |
| 5.6 | Create `Chat/UserBubble.tsx` — user message with timestamp | 15m | |
| 5.7 | Create `Chat/AssistantCard.tsx` — AI response with sections, citations, confidence footer | 45m | |
| 5.8 | Create `Chat/StreamingAnswer.tsx` — animated streaming skeleton | 20m | |
| 5.9 | Create `Chat/SafeRefusalCard.tsx` — purple shield, refusal reason, next actions | 25m | |
| 5.10 | Create `Chat/GeneralKnowledgeToggle.tsx` — patient-specific vs general toggle | 15m | |
| 5.11 | Create `Chat/HowItWorksRail.tsx` — right rail: step-by-step guide | 25m | |
| 5.12 | Build `chat/page.tsx` — SCR-013 (landing hero, suggestions ×4, composer) | 30m | |
| 5.13 | Build `chat/new/page.tsx` — SCR-011 (context chip, toggle, landing hero small, prompt grid, how-it-works rail) | 40m | |
| 5.14 | Build `chat/[id]/page.tsx` — SCR-012 (safe refusal) + SCR-014 (cited answer with evidence rail) | 45m | |
| 5.15 | Test: chat landing, thread creation, message sending, streaming, refusal state | 30m | Vitest |

**Phase 5 Exit Gate**: Full chat lifecycle works: landing → new thread → send message → receive cited answer or safe refusal.

---

### PHASE 6: Evidence & Citations (Est. 3 hours)

**Goal**: Evidence rail, citation cards, inline citations, document viewer modal.

| # | Task | Est. | API |
|---|------|------|-----|
| 6.1 | Create `Evidence/Rail.tsx` — right panel: citation cards + retrieval stepper | 30m | |
| 6.2 | Create `Evidence/CitationCard.tsx` — source document card with snippet, confidence, metadata | 25m | |
| 6.3 | Create `Evidence/CitationLoading.tsx` — skeleton state: "Retrieving..." | 10m | |
| 6.4 | Create `Evidence/InlineCitation.tsx` — blue `[1]` link in answer text | 10m | |
| 6.5 | Create `Evidence/DocumentViewerModal.tsx` (SCR-019) — 3-column: thumbnails (176px) + PDF page (524px) + citation details (300px) | 1h | |
| 6.6 | Create `Evidence/CitationDetails.tsx` — right panel: metadata, snippet, verification | 20m | |
| 6.7 | Create `Evidence/NoEvidenceRail.tsx` — empty state: "No supporting evidence found" | 15m | |
| 6.8 | Create `Evidence/RetrievalStepper.tsx` — 3-step: Retrieving → Validating → Streaming | 15m | |
| 6.9 | Create `Evidence/VerificationChecklist.tsx` — source integrity, permission, sensitivity | 15m | |
| 6.10 | Test: evidence rail renders, citation click opens viewer, stepper animation | 15m | Vitest |

**Phase 6 Exit Gate**: Citations display inline, citation viewer modal works, evidence rail loads asynchronously.

---

### PHASE 7: Documents & OCR Module (Est. 5 hours)

**Goal**: OCR dashboard, OCR review, batch upload modal, semantic search.

| # | Task | Est. | API |
|---|------|------|-----|
| 7.1 | Create API module: `lib/api/documents.ts` | 20m | List, upload, OCR, search |
| 7.2 | Create `Document/UploadDropzone.tsx` — drag-and-drop area with file type hints | 30m | |
| 7.3 | Create `Document/UploadDropzoneCompact.tsx` — smaller version for modals | 15m | |
| 7.4 | Create `Document/DocumentsTable.tsx` — table with Name, Patient, Type, Status, OCR, Date columns | 40m | |
| 7.5 | Create `Document/BatchUploadModal.tsx` — multi-file upload with progress (SCR-017) | 40m | |
| 7.6 | Create `Document/UploadFileTable.tsx` — file rows with progress bars | 20m | |
| 7.7 | Create `Document/OCRPipelineStepper.tsx` — 5-step: Upload → OCR → Chunk → Embed → Ready | 20m | |
| 7.8 | Create `Document/OCRReviewPage.tsx` — review interface (SCR-016) | 40m | |
| 7.9 | Create `Document/LowConfidenceBanner.tsx` — red alert banner | 10m | |
| 7.10 | Create `Document/ScannedPagePane.tsx` — preview of scanned page | 20m | |
| 7.11 | Create `Document/ExtractedTextPane.tsx` — OCR text with low-confidence highlights | 20m | |
| 7.12 | Create `Document/ProcessingTimeline.tsx` — upload → OCR → review → index | 15m | |
| 7.13 | Create `Document/FailureReasonsCard.tsx` — warning list with checklist | 15m | |
| 7.14 | Create `Document/SemanticSearchPanel.tsx` — query input + matching chunk cards | 25m | |
| 7.15 | Create `Document/MatchingChunkCard.tsx` — chunk text + confidence % | 15m | |
| 7.16 | Build `documents/page.tsx` — SCR-015 (upload dropzone, search bar, table ×48 rows, semantic search panel, storage donut) | 30m | |
| 7.17 | Build `documents/[id]/review/page.tsx` — SCR-016 (review pane, OCR text, timeline, failure reasons) | 30m | |
| 7.18 | Build `documents/upload/page.tsx` — SCR-017 (batch upload modal route, file table, pipeline stepper) | 20m | |
| 7.19 | Build `documents/[id]/page.tsx` — SCR-018 (document pages preview) | 20m | |
| 7.20 | Test: upload flow, table rendering, OCR review interface | 20m | Vitest |

**Phase 7 Exit Gate**: Document upload flow works, OCR review renders, semantic search panel interactive.

---

### PHASE 8: Access Control (Est. 2 hours)

**Goal**: Access denied screen, access request justification modal.

| # | Task | Est. | API |
|---|------|------|-----|
| 8.1 | Create API module: `lib/api/access.ts` | 15m | `POST /api/v1/access-requests` |
| 8.2 | Create `Access/DeniedPanel.tsx` — shield-lock icon, reason, request details grid | 25m | |
| 8.3 | Create `Access/RequestDetailsGrid.tsx` — 2×2 grid: Patient, Resource, Reason, Audit | 20m | |
| 8.4 | Create `Access/NextActionsRail.tsx` — "What you can do next" + "Why blocked" | 20m | |
| 8.5 | Create `Access/RequestModal.tsx` — full form: patient summary, selects ×4, purpose radios, justification textarea, explainer timeline (SCR-022) | 45m | |
| 8.6 | Create `Access/ExplainerTimeline.tsx` — right rail: shield, clock, user, bell, lock | 20m | |
| 8.7 | Create `Access/PurposeRadioCard.tsx` — radio cards: Immediate, Care Coord, Records Review | 15m | |
| 8.8 | Create `Access/JustificationTextarea.tsx` — textarea with char counter (500 max) | 10m | |
| 8.9 | Test: denied panel renders, request modal submits form, validation works | 15m | Vitest |

**Phase 8 Exit Gate**: Access denied flow complete, request modal validates and submits.

---

### PHASE 9: Audit Module (Est. 2.5 hours)

**Goal**: Audit events log with filter bar, event drawer, compliance cards.

| # | Task | Est. | API |
|---|------|------|-----|
| 9.1 | Create API module: `lib/api/audit.ts` | 15m | `GET /api/v1/audit/events` |
| 9.2 | Create `Audit/MetricCard.tsx` — KPI with trend arrow, colored icon | 20m | |
| 9.3 | Create `Audit/FilterBar.tsx` — horizontal filters: User, Patient, Action, Date, Result | 25m | |
| 9.4 | Create `Audit/EventsTable.tsx` — table with Timestamp, User, Role, Patient, Action, Resource, Result (1,248 events, paginated) | 45m | |
| 9.5 | Create `Audit/EventDrawer.tsx` — right drawer: tabs Overview/Raw, metadata, context (SCR-023) | 40m | |
| 9.6 | Create `Audit/ComplianceCard.tsx` — "100% sensitive query logging" card | 15m | |
| 9.7 | Build `audit/page.tsx` — SCR-023 (metric cards ×4, filter bar, events table, event drawer, compliance cards ×2) | 30m | |
| 9.8 | Test: table renders, filter works, drawer opens with event details | 15m | Vitest |

---

### PHASE 10: Metrics Module (Est. 2 hours)

**Goal**: Impact quality dashboard with charts and feedback.

| # | Task | Est. | API |
|---|------|------|-----|
| 10.1 | Create API module: `lib/api/metrics.ts` | 15m | `GET /api/v1/metrics/summary` |
| 10.2 | Create `viz/QualitySafetyChart.tsx` — area + line overlay chart | 20m | |
| 10.3 | Create `viz/WorkflowImpactTable.tsx` — 4 workflows with baseline/actual/time saved/% | 25m | |
| 10.4 | Create `viz/UserFeedbackCard.tsx` — rating 4.7/5, stars, quote list | 20m | |
| 10.5 | Create `viz/StorageDonutChart.tsx` — donut with legend | 20m | |
| 10.6 | Build `metrics/page.tsx` — SCR-024 (metric cards ×4, date range filter, trend chart, bar chart, quality chart, workflow table, feedback card) | 30m | |
| 10.7 | Test: charts render, date filter works, data flows from API | 15m | Vitest |

---

### PHASE 11: Settings Module (Est. 2 hours)

**Goal**: Profile & system preferences with local subnav.

| # | Task | Est. | API |
|---|------|------|-----|
| 11.1 | Create API module: `lib/api/settings.ts` | 15m | `GET /api/v1/users/me/preferences` |
| 11.2 | Build `settings/page.tsx` — SCR-025 (local subnav 9 items, profile card, preferences card with 7 form rows, display card with segments, security card, right rail ×4) | 1.5h | |
| 11.3 | Test: subnav navigation, form controls work, preferences save | 15m | Vitest |

---

### PHASE 12: Global Overlays (Est. 2 hours)

**Goal**: Environment selector dropdown (built into Topbar) + polish command palette.

| # | Task | Est. | Validate |
|---|------|------|----------|
| 12.1 | Build environment selector dropdown — 4 option rows (Synthetic, Sandbox, Training, Production) anchored to Topbar pill (SCR-027) | 30m | Dropdown opens/closes |
| 12.2 | Polish CommandPalette (SCR-020) — empty state with keyboard tips, recent items, quick commands section | 30m | |
| 12.3 | Global toast system — wire up success/error toast for cross-screen use | 20m | |
| 12.4 | Test: overlays don't break layout, z-index stacking correct | 15m | |

---

### PHASE 13: Integration Wiring & Polish (Est. 4 hours)

**Goal**: Connect all screens to real API, ensure data flow, add loading/error/empty states everywhere.

| # | Task |
|---|------|
| 13.1 | Wire dashboard to `GET /api/v1/dashboard/summary` — handle empty (SCR-005) vs populated (SCR-003) |
| 13.2 | Wire patient list to `GET /api/v1/patients/search` — handle empty state (SCR-009) |
| 13.3 | Wire patient overview to `GET /api/v1/patients/{id}/overview` — loading → data → error states |
| 13.4 | Wire AI summary to `POST /api/v1/patients/{id}/ai-summary/generate` — streaming SSE |
| 13.5 | Wire medication review to `POST /api/v1/patients/{id}/medication-review` |
| 13.6 | Wire chat threads to `GET/POST /api/v1/chat-threads` |
| 13.7 | Wire chat messages to `POST /api/v1/chat` — handle cited answer (200) vs safe refusal (422) |
| 13.8 | Wire documents to `GET /api/v1/documents`, upload to `POST /api/v1/documents/batch` |
| 13.9 | Wire audit to `GET /api/v1/audit/events` |
| 13.10 | Wire metrics to `GET /api/v1/metrics/summary` |
| 13.11 | Wire access requests to `POST /api/v1/access-requests` |
| 13.12 | Wire global search to `GET /api/v1/search/global` |
| 13.13 | Wire settings to `GET /api/v1/users/me/preferences` |
| 13.14 | Add loading skeletons to all data-dependent screens |
| 13.15 | Add error boundaries and retry buttons to all pages |
| 13.16 | Add empty-state components to all list/detail views |

---

### PHASE 14: Testing (Est. 6 hours)

**Goal**: Reach 80% test coverage on components and pages.

| # | Task |
|---|------|
| 14.1 | Write tests for all shadcnUI overrides (button variants, input states) |
| 14.2 | Write tests for AppShell components (Topbar, Sidebar, CommandPalette) |
| 14.3 | Write tests for Auth components (LoginCard, MFACard, form validation) |
| 14.4 | Write tests for Patient components (DetailHeader, AISummaryCard, MedicationList) |
| 14.5 | Write tests for Chat components (Composer, UserBubble, AssistantCard, SafeRefusalCard) |
| 14.6 | Write tests for Evidence components (CitationCard, DocumentViewerModal) |
| 14.7 | Write tests for Document components (UploadDropzone, DocumentsTable, BatchUploadModal) |
| 14.8 | Write tests for Access components (DeniedPanel, RequestModal) |
| 14.9 | Write tests for Audit components (EventsTable, EventDrawer, FilterBar) |
| 14.10 | Write tests for Metrics components (charts render, data mapping) |
| 14.11 | Write tests for API client (auth header injection, error handling, response parsing) |
| 14.12 | Write page-level integration tests for critical flows |
| 14.13 | `rtk vitest run --coverage` — verify ≥80% |
| 14.14 | `rtk next build` — verify production build passes |

---

### PHASE 15: Final QA & Handoff (Est. 2 hours)

| # | Task |
|---|------|
| 15.1 | Visual comparison: each screen against Figma reference PNG (8px tolerance) |
| 15.2 | Component audit: verify all shadcnUI components initialized, no raw HTML replacing them |
| 15.3 | Token audit: verify all colors/fonts/spacing use Tailwind theme tokens, no hardcoded values |
| 15.4 | Accessibility check: keyboard nav, focus rings, ARIA labels on all interactive elements |
| 15.5 | Responsive check: app shell collapses sidebar on narrow viewports |
| 15.6 | `rtk lint` — zero warnings |

---

## 8. Execution Timeline

| Phase | Description | Screens | Est. Hours | Cumulative |
|-------|-------------|---------|------------|------------|
| 0 | Project Scaffold & Foundation | — | 3 | 3 |
| 1 | App Shell | — | 4 | 7 |
| 2 | Auth Module | 2 | 3 | 10 |
| 3 | Dashboard Module | 4 | 4 | 14 |
| 4 | Patients Module | 6 | 8 | 22 |
| 5 | Chat Module | 3 | 5 | 27 |
| 6 | Evidence & Citations | 2 | 3 | 30 |
| 7 | Documents & OCR | 4 | 5 | 35 |
| 8 | Access Control | 2 | 2 | 37 |
| 9 | Audit Module | 1 | 2.5 | 39.5 |
| 10 | Metrics Module | 1 | 2 | 41.5 |
| 11 | Settings Module | 1 | 2 | 43.5 |
| 12 | Global Overlays | 2 | 2 | 45.5 |
| 13 | Integration Wiring | — | 4 | 49.5 |
| 14 | Testing (80% coverage) | — | 6 | 55.5 |
| 15 | Final QA & Handoff | — | 2 | 57.5 |
| **TOTAL** | | **25 screens** | **~58 hours** | |

---

## 9. API Endpoint → Screen Mapping

| API Endpoint | Method | Screens Consuming |
|---|---|---|
| `/api/v1/auth/login` | POST | SCR-001 |
| `/api/v1/auth/mfa/verify` | POST | SCR-002 |
| `/api/v1/dashboard/summary` | GET | SCR-003, 005 |
| `/api/v1/patients/search` | GET | SCR-006, 009 |
| `/api/v1/patients/{id}/overview` | GET | SCR-007, 021 |
| `/api/v1/patients/{id}/ai-summary/generate` | POST | SCR-010 (SSE) |
| `/api/v1/patients/{id}/medication-review` | POST | SCR-008 |
| `/api/v1/chat-threads` | GET, POST | SCR-011, 013 |
| `/api/v1/chat` | POST | SCR-012, 014 |
| `/api/v1/chat/queries/{queryId}/citations` | GET | SCR-019 |
| `/api/v1/documents` | GET | SCR-015 |
| `/api/v1/documents/batch` | POST | SCR-017 |
| `/api/v1/documents/{id}/extracted-text` | GET | SCR-016 |
| `/api/v1/documents/{id}/pages/{page}` | GET | SCR-018 |
| `/api/v1/access-requests` | POST | SCR-022 |
| `/api/v1/audit/events` | GET | SCR-023 |
| `/api/v1/metrics/summary` | GET | SCR-024 |
| `/api/v1/search/global` | GET | SCR-020 |
| `/api/v1/users/me/preferences` | GET, PUT | SCR-025 |

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| shadcnUI v4 breaking changes from old v3 | MEDIUM | HIGH | Pin shadcn@4.5.0, init fresh instead of migrating old components |
| Tailwind CSS v4 migration differences | MEDIUM | MEDIUM | Use `@tailwindcss/postcss` plugin; CSS-first config with theme mapping |
| Streaming SSE not supported by backend yet | LOW | MEDIUM | Fallback to polling in chat stream client; backend has `chat_stream.py` route |
| Recharts v3 API changes | LOW | LOW | Use v3.8.x API, test chart components early in Phase 3 |
| Figma→code visual fidelity drift | MEDIUM | MEDIUM | Reference exact Figma measurements in component specs; compare screenshots |
| Missing backend endpoints | LOW | HIGH | Backend has 14 route modules covering all screens; verify each before wiring |
| Command palette performance | LOW | MEDIUM | Debounce search (250ms), limit results per section (5 each) |

---

## 11. Component Reuse Strategy

The shadcnUI base components are the foundation. Domain components compose them:

```
shadcnUI primitives → Domain components → Pages

Example: Patient/DetailHeader
  ├── ui/avatar (shadcn)
  ├── ui/badge (shadcn) → status chip
  ├── ui/button (shadcn) → bookmark, kebab menu
  └── Patient/ContextChip (domain) → patient name + MRN
```

**Maximize reuse across screens**:
- `Patient/ContextChip` used in: SCR-007, 008, 010, 011, 012, 014
- `Evidence/CitationCard` used in: SCR-007, 008, 010, 014, 015, 019
- `Chat/Composer` used in: SCR-003, 010, 011, 012, 013, 014
- `Card/Metric` (shadcn card wrapper) used in: SCR-003, 006, 023, 024

---

## 12. Quick-Start Sprint (Recommended First Milestone)

Build these in order to validate the entire pipeline:

| Order | Task | Est. | Why First |
|-------|------|------|-----------|
| 1 | Phase 0 (scaffold) | 3h | Prerequisite for everything |
| 2 | Phase 1 (app shell) | 4h | All screens depend on layout |
| 3 | Phase 2 (auth) | 3h | Gate for authenticated routes |
| 4 | Phase 3 (dashboard) | 4h | Most complex screen — proves component library works |

**Sprint Exit Gate**: Dashboard SCR-003 renders with KPI cards, charts, tables, and sidebar navigation. If this works, the full plan is validated.

---

## 13. Validation Gates

| Gate | Check | Must Pass Before |
|------|-------|-----------------|
| G1 | `next build` succeeds with zero errors | Phase 1 |
| G2 | All shadcnUI components initialize without import errors | Phase 1 |
| G3 | App shell renders Topbar + Sidebar + Content at correct dimensions (64px/256px) | Phase 2 |
| G4 | Auth flow: login → MFA → redirect to dashboard | Phase 3 |
| G5 | Dashboard renders populated state with real data from API | Phase 4 |
| G6 | All 25 screen routes render without crashing | Phase 13 |
| G7 | All API endpoints wired, loading/error/empty states present | Phase 14 |
| G8 | Test coverage ≥80% | Phase 15 |
| G9 | `rtk lint` zero warnings | Phase 15 |
| G10 | Visual comparison passes against Figma PNG references | Phase 16 |

---

## 14. Acceptance Criteria

- [ ] **All 25 screens** built as TanStack Start pages with correct routes
- [ ] **All ~80 domain components** created using shadcnUI primitives
- [ ] **All design tokens** mapped to Tailwind CSS custom properties (no hardcoded colors)
- [ ] **All 18 shadcnUI base components** initialized and available
- [ ] **All API endpoints** wired with loading, error, and empty states
- [ ] **App shell** matches Figma dimensions (sidebar 256px, topbar 64px)
- [ ] **Streaming chat** works with SSE for AI summary and chat answers
- [ ] **Command palette** (⌘K) searches across patients, documents, threads
- [ ] **Test coverage ≥80%** on components and API client
- [ ] **Accessibility**: keyboard navigation, focus management, ARIA labels
- [ ] **Responsive**: sidebar collapses, content reflows on narrow viewports
- [ ] **Zero hardcoded styles** — all colors, fonts, spacing from design tokens

---

> **✅ CONFIRMED & APPROVED**: This plan covering 25 screens, ~80 domain components, 18 shadcnUI base components, 14 API modules, and ~58 estimated hours of implementation has been finalized and approved for execution.
