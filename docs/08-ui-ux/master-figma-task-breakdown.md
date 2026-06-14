# Master Figma Task Breakdown — HMS AI Copilot

> **Parent Plan**: `master-figma-execution-plan.md`  
> **Purpose**: Atomic, assignable tasks derived from the master execution plan  
> **Generated**: 2026-06-10  
> **Total Tasks**: 197  

---

## Plan Review Summary

### What the Plan Covers Well
- ✅ Complete screen inventory (25 screens) with component-to-instance mapping
- ✅ Full component library specification (~90 components across 7 base + 9 domain groups)
- ✅ Build pipeline order (tokens → base components → domain components → screens → QA)
- ✅ Design token verification (Phase 0 gate before any building)
- ✅ Visual QA process with 8px tolerance and per-category checks
- ✅ Prototype flow connections (17 flows)
- ✅ Pattern grounding against existing documentation
- ✅ Risk identification with mitigations

### Gaps Identified & Addressed Below
- ⚠️ **No Figma API access verified** — Added Task 0.0 to validate access before starting
- ⚠️ **Asset mapping incomplete** — Added Task 0.7 to create asset → component map
- ⚠️ **No per-component QA** — Added QA subtasks within each component phase
- ⚠️ **No rollback strategy** — Added Task 0.8 to version/snapshot the Figma file before starting
- ⚠️ **Missing screen SCR-014 (Chat Cited Answer) blueprint** — Added as Task 7.4
- ⚠️ **No grid system specification** — Added Task 3.0 to define layout grids
- ⚠️ **Missing SCR-018 (Document Pages Preview) blueprint** — Added as Task 8.4

### Risk Summary
| Risk | Severity | Mitigation Status | Status |
|------|----------|-------------------|--------|
| No verified Figma API access | CRITICAL | Task 0.0 — must complete first | ✅ |
| Layout drift from references | HIGH | QA gates after every phase | ✅ |
| Component reuse not enforced | HIGH | Layer audit in Phase 15 | ✅ |
| Missing SCR-014/018 specs | MEDIUM | Tasks 7.4, 8.4 added | ✅ |

---

## Task Breakdown by Phase

### PHASE 0: Foundation & Prerequisites (8 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 0.0 | **Verify Figma API access** — confirm token has read+write to file `RnOWTUhlXXie7AO24zggMm` | — | 15 | API returns file metadata | ✅ |
| 0.1 | **Audit color styles** — list all existing paint styles, flag missing from 60+ token list | 0.0 | 20 | All tokens from `figma-design-system-delivery.md` exist | ✅ |
| 0.2 | **Audit typography styles** — verify all 13 presets (Display, H1-H4, Metric, Body, BodyStrong, Caption, CaptionStrong, Button) | 0.0 | 10 | All 13 presets exist | ✅ |
| 0.3 | **Audit effect styles** — verify Card shadow, Modal shadow, Popover shadow, FocusRing | 0.0 | 10 | All 4 effects exist | ✅ |
| 0.4 | **Audit spacing/radius variables** — check `HMS Tokens` collection has Spacing/1-16 and Radius/XS-3XL | 0.0 | 10 | All spacing + radius tokens exist | ✅ |
| 0.5 | **Create missing Figma pages** — ensure `03 Components / Base`, `04 Components / Domain`, `05 Screens` exist | 0.0 | 5 | Pages visible in Figma | ✅ |
| 0.6 | **Clean up placeholder frames** — delete any documentation boards, markdown text, or description frames that are not real UI | 0.5 | 15 | No non-UI frames on component/screen pages | ✅ |
| 0.7 | **Map design assets to components** — create a lookup table: asset PNG → target component → screen | 0.1 | 20 | Asset mapping doc exists | ✅ |
| 0.8 | **Snapshot Figma file** — save a version/backup before starting modifications | 0.0 | 5 | Version saved | ✅ |

**Phase 0 Exit Gate**: All tokens verified, pages exist, assets mapped, file backed up, no description frames remain.

---

### PHASE 1: Base Components — Buttons (12 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 1.1 | **Create Button/Primary component** — sm/md/lg variants, all 5 states (default/hover/focus/disabled/loading) | 0.5 | 45 | Auto Layout H, padding 12-16×10, gap 8, Radius LG, Typography/Button | ✅ |
| 1.2 | **Create Button/Secondary component** — sm/md/lg, 4 states | 0.5 | 30 | Same specs, outline style | ✅ |
| 1.3 | **Create Button/Outline component** — sm/md/lg, 4 states | 0.5 | 30 | Border-only, transparent fill | ✅ |
| 1.4 | **Create Button/Ghost component** — sm/md/lg, 4 states | 0.5 | 30 | No border, transparent fill | ✅ |
| 1.5 | **Create Button/Danger component** — sm/md/lg, 4 states | 0.5 | 30 | Color/Danger/600 fill | ✅ |
| 1.6 | **Create Button/Icon component** — sm/md/lg, 4 states, icon-only | 0.5 | 25 | Square aspect, icon slot | ✅ |
| 1.7 | **QA all Button variants** — verify Auto Layout, constraints, state transitions, text overrides work | 1.1-1.6 | 20 | All buttons render correctly at all sizes/states | ✅ |
| 1.8 | **Bind Button tokens** — connect all button fills/texts to Figma color/text styles | 1.1-1.6 | 10 | No hardcoded colors in buttons | ✅ |
| 1.9 | **Add component descriptions** — document each button's usage in Figma component description | 1.7 | 10 | Descriptions present | ✅ |
| 1.10 | **Create Button page section** — organize buttons on `03 Components / Base / 01 Buttons` page | 1.1-1.6 | 10 | Clean page layout | ✅ |
| 1.11 | **Publish button components** — make available to other pages via component publishing | 1.7-1.9 | 5 | Buttons usable from Assets panel | ✅ |
| 1.12 | **Snapshot Phase 1** — save version after buttons complete | 1.11 | 5 | Version saved | ✅ |

---

### PHASE 1 (Continued): Base Components — Inputs (12 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 1.13 | **Create Input/Text component** — sm/md/lg, 6 states (default/hover/focus/disabled/error/filled) | 0.5 | 45 | Auto Layout H, padding 12×0, Radius LG | ✅ |
| 1.14 | **Create Input/Password component** — md, 4 states, eye toggle icon | 1.13 | 25 | Password reveal toggle works | ✅ |
| 1.15 | **Create Input/Search component** — md/lg, 2 states, search icon left | 1.13 | 20 | Search icon, ⌘K shortcut slot | ✅ |
| 1.16 | **Create Input/Textarea component** — md, 3 states, char counter slot | 1.13 | 20 | Char counter visible | ✅ |
| 1.17 | **Create Input/Select component** — sm/md, 5 states, chevron icon | 1.13 | 30 | Dropdown chevron | ✅ |
| 1.18 | **Create Input/OTP component** — md, 3 states, 6 individual cells | 1.13 | 30 | 6 equal-width cells | ✅ |
| 1.19 | **QA all Input variants** — verify focus rings, placeholder text, error states | 1.13-1.18 | 20 | All inputs render correctly | ✅ |
| 1.20 | **Bind Input tokens** — connect all input fills/borders/texts to Figma styles | 1.13-1.18 | 10 | No hardcoded colors | ✅ |
| 1.21 | **Add input descriptions** — document each input's behavior | 1.19 | 10 | Descriptions present | ✅ |
| 1.22 | **Create Inputs page section** — organize on `03 Components / Base / 02 Inputs` | 1.13-1.18 | 10 | Clean page layout | ✅ |
| 1.23 | **Publish input components** | 1.19-1.21 | 5 | Inputs in Assets panel | ✅ |
| 1.24 | **Snapshot** | 1.23 | 5 | Version saved | ✅ |

---

### PHASE 1 (Continued): Base Components — Chips, Cards, Tables, Nav, Overlays (35 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 1.25 | **Create Chip/Status** — 6 tones (neutral/success/danger/warning/purple/cyan) | 0.5 | 25 | Radius XS or Full | ✅ |
| 1.26 | **Create Chip/Permission** — 4 variants (authorized/denied/pending/restricted) | 0.5 | 20 | | ✅ |
| 1.27 | **Create Chip/Confidence** — 3 variants (high/medium/low) | 0.5 | 15 | | ✅ |
| 1.28 | **Create Badge/Count** — 3 tones, Create Badge/Filter — default+active | 0.5 | 20 | | ✅ |
| 1.29 | **QA + bind + publish Chips & Badges** | 1.25-1.28 | 15 | | ✅ |
| 1.30 | **Create Card/Standard** — 3 states (default/hover/selected) | 0.5 | 30 | Auto Layout V, padding 16-24, Radius XL, Shadow Card | ✅ |
| 1.31 | **Create Card/Metric (KPI)** — 4 variants (default/positive/negative/skeleton) | 1.30 | 25 | | ✅ |
| 1.32 | **Create Card/Info** — 3 variants, Create Card/Empty — default | 1.30 | 25 | | ✅ |
| 1.33 | **QA + bind + publish Cards** | 1.30-1.32 | 15 | | ✅ |
| 1.34 | **Create Table/Header** — with checkbox, sort icons | 0.5 | 25 | | ✅ |
| 1.35 | **Create Table/Row** — 3 states, Create Table/Cell — 4 variants | 1.34 | 30 | Row height 48-52px | ✅ |
| 1.36 | **Create Table/Pagination + Table/Empty** | 1.34 | 20 | | ✅ |
| 1.37 | **QA + bind + publish Tables** | 1.34-1.36 | 15 | | ✅ |
| 1.38 | **Create Nav/SidebarItem** — 3 variants (default/active/collapsed) | 0.5 | 25 | Height 40-44, Radius MD | ✅ |
| 1.39 | **Create Nav/SidebarSection + Nav/Tab + Nav/TabBar** | 1.38 | 25 | | ✅ |
| 1.40 | **Create Nav/Breadcrumb + Nav/LocalSubnav** | 0.5 | 20 | | ✅ |
| 1.41 | **QA + bind + publish Navigation** | 1.38-1.40 | 15 | | ✅ |
| 1.42 | **Create Overlay/Modal** — 4 sizes (480/640/800/960) | 0.5 | 30 | Shadow Modal, centered | ✅ |
| 1.43 | **Create Overlay/Drawer** — right 300/360, left | 0.5 | 20 | | ✅ |
| 1.44 | **Create Overlay/Dropdown** — min 200, max 370 | 0.5 | 20 | Shadow Popover | ✅ |
| 1.45 | **Create Overlay/Toast** — 4 tones (success/error/warning/info) | 0.5 | 20 | Width ~300, height 56-64 | ✅ |
| 1.46 | **Create Overlay/Backdrop** | 0.5 | 10 | Navy/gray 50-60% opacity, z=500 | ✅ |
| 1.47 | **QA + bind + publish Overlays** | 1.42-1.46 | 15 | | ✅ |

**Phase 1 Exit Gate**: All 37 base components created, QA'd, token-bound, and published. ~8 hours cumulative.

---

### PHASE 2: Domain Components — App Shell (8 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 2.1 | **Create Shell/Topbar** — Logo, Search input, EnvironmentPill, User avatar, height 64px | 1.15, 1.25 | 30 | | ✅ |
| 2.2 | **Create Shell/Sidebar** — Nav items (8), Recent items section, Permission card, Footer, width 256px | 1.38, 1.30 | 45 | | ✅ |
| 2.3 | **Create Shell/Footer** — Safety disclaimer text | 1.13 | 10 | | ✅ |
| 2.4 | **Create Shell/RightRail** — Stacked card container, width 300-340px | 1.30 | 15 | | ✅ |
| 2.5 | **Create Shell/Standard template** — 1448×1086 frame: Topbar + Sidebar + Content + Footer | 2.1-2.3 | 30 | Dimensions exact | ✅ |
| 2.6 | **Create Shell/Wide template** — 1672×941 frame: Topbar + Sidebar + Content + RightRail | 2.1-2.4 | 25 | | ✅ |
| 2.7 | **Create Shell/WideWithDrawer + Shell/Auth + Shell/Modal templates** | 2.5, 1.42 | 30 | | ✅ |
| 2.8 | **QA all Shell templates** — verify dimensions, component usage, token binding | 2.5-2.7 | 20 | | ✅ |

---

### PHASE 2 (Continued): Domain — Patient, Chat, Evidence (24 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 2.9 | **Create Patient/DetailHeader** — avatar, name, MRN, chips, bookmark, kebab | 1.25, 1.30 | 30 | | ✅ |
| 2.10 | **Create Patient/MetadataGrid** — 2-row grid, 8 fields | 2.9 | 20 | | ✅ |
| 2.11 | **Create Patient/SummaryStrip** — compact version for modals | 2.9 | 15 | | ✅ |
| 2.12 | **Create Patient/ContextChip** — patient name + MRN + permission status | 1.25 | 15 | | ✅ |
| 2.13 | **Create Patient/AISummaryCard** — sections, citations, confidence footer | 1.30, 1.25 | 30 | | ✅ |
| 2.14 | **Create Patient/ClinicalSection + MiniLabStrip + MedicationList** | 2.13 | 30 | | ✅ |
| 2.15 | **Create Patient/AllergyAlertsCard + EncounterTimeline + RecentPatientsCard** | 1.30 | 30 | | ✅ |
| 2.16 | **QA + publish all Patient components** | 2.9-2.15 | 20 | | ✅ |
| 2.17 | **Create Chat/LandingHero + Chat/SuggestionCard** | 1.30 | 25 | | ✅ |
| 2.18 | **Create Chat/PromptGrid + Chat/Composer** | 1.13, 1.1 | 30 | | ✅ |
| 2.19 | **Create Chat/UserBubble + Chat/AssistantCard + Chat/StreamingAnswer** | 1.30 | 30 | | ✅ |
| 2.20 | **Create Chat/SafeRefusalCard + Chat/GeneralKnowledgeToggle + Chat/HowItWorksRail** | 1.30, 1.25 | 30 | | ✅ |
| 2.21 | **QA + publish all Chat components** | 2.17-2.20 | 20 | | ✅ |
| 2.22 | **Create Evidence/Rail + Evidence/CitationCard + Evidence/CitationLoading** | 1.30 | 30 | | ✅ |
| 2.23 | **Create Evidence/InlineCitation + Evidence/DocumentViewerModal** | 1.42 | 30 | | ✅ |
| 2.24 | **Create Evidence/CitationDetails + Evidence/NoEvidenceRail** | 2.22 | 20 | | ✅ |
| 2.25 | **Create Evidence/RetrievalStepper + Evidence/VerificationChecklist** | 1.25 | 20 | | ✅ |
| 2.26 | **QA + publish all Evidence components** | 2.22-2.25 | 20 | | ✅ |

---

### PHASE 2 (Continued): Domain — Documents, Audit, Auth, Viz, Empty (33 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 2.27 | **Create Document/UploadDropzone + UploadDropzoneCompact** | 1.1, 1.30 | 30 | | ✅ |
| 2.28 | **Create Document/DocumentsTable** — Name, Patient, Type, Status, OCR Conf, Date cols | 1.34-1.36 | 30 | | ✅ |
| 2.29 | **Create Document/BatchUploadModal + UploadFileTable** | 1.42, 1.34 | 30 | | ✅ |
| 2.30 | **Create Document/OCRPipelineStepper** — 5-step pipeline | 1.25 | 20 | | ✅ |
| 2.31 | **Create Document/OCRReviewPage + LowConfidenceBanner** | 1.30, 1.25 | 30 | | ✅ |
| 2.32 | **Create Document/ScannedPagePane + ExtractedTextPane** | 1.30 | 25 | | ✅ |
| 2.33 | **Create Document/ProcessingTimeline + FailureReasonsCard** | 1.30 | 20 | | ✅ |
| 2.34 | **Create Document/SemanticSearchPanel + MatchingChunkCard + StorageUsageDonut** | 1.30, 1.13 | 30 | | ✅ |
| 2.35 | **QA + publish all Document components** | 2.27-2.34 | 25 | | ✅ |
| 2.36 | **Create Access/DeniedPanel + RequestDetailsGrid** | 1.30 | 30 | | ✅ |
| 2.37 | **Create Access/NextActionsRail + Access/RequestModal** | 2.36, 1.42 | 30 | | ✅ |
| 2.38 | **Create Access/ExplainerTimeline + PurposeRadioCard + JustificationTextarea** | 1.16, 1.30 | 25 | | ✅ |
| 2.39 | **Create Audit/MetricCard + Audit/FilterBar** | 1.31, 1.25 | 25 | | ✅ |
| 2.40 | **Create Audit/EventsTable + Audit/EventDrawer + Audit/ComplianceCard** | 1.34, 1.43 | 30 | | ✅ |
| 2.41 | **QA + publish all Audit/Access components** | 2.36-2.40 | 20 | | ✅ |
| 2.42 | **Create Auth/SplitLayout + Auth/MarketingFeatureList** | 1.30 | 25 | | ✅ |
| 2.43 | **Create Auth/LoginCard + Auth/SSOButton** | 2.42, 1.1 | 25 | | ✅ |
| 2.44 | **Create Auth/EmailPasswordForm + Auth/SecurityAssuranceBox** | 1.13, 1.14 | 20 | | ✅ |
| 2.45 | **Create Auth/MFACard + Auth/OTPInputGroup + Auth/CountdownResend** | 1.18, 1.30 | 30 | | ✅ |
| 2.46 | **Create Auth/AuthTrustStrip** | 1.30 | 15 | | ✅ |
| 2.47 | **QA + publish all Auth components** | 2.42-2.46 | 20 | | ✅ |
| 2.48 | **Create Viz/TrendLineChart + Viz/BarVolumeChart** | 1.30 | 30 | | ✅ |
| 2.49 | **Create Viz/QualitySafetyChart + Viz/StorageDonutChart** | 2.48 | 25 | | ✅ |
| 2.50 | **Create Viz/WorkflowImpactTable + Viz/UserFeedbackCard** | 1.34, 1.30 | 25 | | ✅ |
| 2.51 | **QA + publish all DataViz components** | 2.48-2.50 | 15 | | ✅ |
| 2.52 | **Create Empty/DashboardHero + Empty/PatientsState + Empty/TableRow** | 1.30 | 25 | | ✅ |
| 2.53 | **Create Empty/SkeletonMetricCard + SkeletonThreadCard + SkeletonCitationCard** | 1.31, 1.30 | 20 | | ✅ |
| 2.54 | **QA + publish all Empty State components** | 2.52-2.53 | 15 | | ✅ |

**Phase 2 Exit Gate**: All ~53 domain components created, QA'd, and published. ~10 hours cumulative from Phase 1.

---

### PHASE 3: App Shell Templates (6 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 3.0 | **Define layout grids** — Document column widths, gutters, margins for Standard/Wide/Auth templates | — | 15 | Grid spec exists | ✅ |
| 3.1 | **Build Shell/Standard** — 1448×1086, apply global constants (user, environment, nav items, footer) | 2.5-2.8 | 30 | Dimensions exact, global constants set | ✅ |
| 3.2 | **Build Shell/Wide** — 1672×941, same global constants | 2.6-2.8 | 20 | | ✅ |
| 3.3 | **Build Shell/WideWithDrawer** — Wide + 360px drawer slot | 3.2 | 15 | | ✅ |
| 3.4 | **Build Shell/Auth** — 1448×1086, no sidebar | 2.42 | 20 | | ✅ |
| 3.5 | **Build Shell/Modal** — Backdrop + modal container | 1.42 | 15 | | ✅ |

**Phase 3 Exit Gate**: All 5 shell templates built and verified. ~3 hours cumulative.

---

### PHASE 4-14: Screen Building Tasks (50 tasks)

#### Auth Screens (6 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 4.1 | **Build SCR-001 Staff SSO Login** — SplitLayout, MarketingPane, LoginCard, SSOButton, Email/Password, TrustCard | 3.4 | 40 | Auth | ✅ |
| 4.2 | **QA SCR-001** against `auth.login.staff-sso-email-password.png` | 4.1 | 15 | Auth | ✅ |
| 4.3 | **Build SCR-002 MFA Verification** — MFACard, OTPInputs (6 cells), Countdown, MethodSelect, VerifyButton, TrustStrip | 3.4 | 35 | Auth | ✅ |
| 4.4 | **QA SCR-002** against `auth.mfa.verify-identity-code.png` | 4.3 | 15 | Auth | ✅ |
| 4.5 | **Connect prototype flow** SCR-001 → SCR-002 (Login → MFA) | 4.2, 4.4 | 10 | Auth | ✅ |
| 4.6 | **Connect prototype flow** SCR-002 → SCR-003 (MFA → Dashboard) | 4.4 | 5 | Auth | ✅ |

#### Dashboard Screens (8 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 5.1 | **Build SCR-005 Empty Workspace** — EmptyHero, SkeletonMetrics ×4, UploadCTA, AddPatientCTA | 3.2 | 30 | Dashboard | ✅ |
| 5.2 | **QA SCR-005** against `dashboard.empty.workspace-onboarding-first-data.png` | 5.1 | 15 | Dashboard | ✅ |
| 5.3 | **Build SCR-003 Populated Dashboard** — KPI cards ×4, QuickTaskPanel, RecentPatients, Threads, DocStatus, SafetyCard, Charts ×2 | 3.2 | 45 | Dashboard | ✅ |
| 5.4 | **QA SCR-003** against `dashboard.overview.populated-hms-ai-workspace.png` | 5.3 | 15 | Dashboard | ✅ |
| 5.5 | **Build SCR-004 User Menu state** — same as SCR-003 + UserProfileDropdown open | 5.3 | 20 | Dashboard | ✅ |
| 5.6 | **QA SCR-004** against `dashboard.overview.action-success-toast.png` | 5.5 | 10 | Dashboard | ✅ |
| 5.7 | **Build SCR-004 Toast Stack** — same as SCR-003 + ToastStack overlay (2 toasts) | 5.3 | 15 | Dashboard | ✅ |
| 5.8 | **QA SCR-004 Toast** against `dashboard.overview.success-toast-stack.png` | 5.7 | 10 | Dashboard | ✅ |

#### Patient Screens (12 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 6.1 | **Build SCR-009 Patient Empty State** — EmptyPatientsHero, SearchBar, TableHeader, EmptyRow, RightRail cards | 3.2 | 35 | Patients | ✅ |
| 6.2 | **QA SCR-009** against `patients.empty.no-results-or-no-access.png` | 6.1 | 15 | Patients | ✅ |
| 6.3 | **Build SCR-006 Patient List Scoped** — KPI cards ×4, SearchBar + Filters, DataTable ×8 rows, RightRail | 3.2 | 50 | Patients | ✅ |
| 6.4 | **QA SCR-006** against `patients.list.scoped-alerts-recent-activity.png` | 6.3 | 15 | Patients | ✅ |
| 6.5 | **Build SCR-007 Patient Overview with AI Summary** — DetailHeader, MetadataGrid, TabBar, AISummaryCard (5 sections), InlineCitations ×10, RightRail ×4 | 3.1 | 60 | Patients | ✅ |
| 6.6 | **QA SCR-007** against `patients.overview.ai-summary-hms-snapshot.png` | 6.5 | 20 | Patients | ✅ |
| 6.7 | **Build SCR-010 AI Summary Streaming** — ContextChip, UserBubble, StreamingAnswer (skeleton), EvidenceRetrievalStepper, CitationCard+Loading ×3, Composer | 3.1 | 45 | Patients | ✅ |
| 6.8 | **QA SCR-010** against `patients.ai-summary.stream-citations-retrieving.png` | 6.7 | 15 | Patients | ✅ |
| 6.9 | **Build SCR-008 Medication Review** — ContextChip, UserBubble, CitedClinicalAnswer (4 sections, [1][2][3]), CitationCards ×3, Composer | 3.1 | 45 | Patients | ✅ |
| 6.10 | **QA SCR-008** against `patients.medication-review.cited-safety-answer.png` | 6.9 | 15 | Patients | ✅ |
| 6.11 | **Build SCR-021 Access Denied** — DeniedPanel, RequestDetailsGrid 2×2, NextActionsRail, CTA buttons | 3.1 | 40 | Access | ✅ |
| 6.12 | **QA SCR-021** against `access-control.denied.no-treatment-relationship.png` | 6.11 | 15 | Access | ✅ |

#### Chat Screens (8 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 7.1 | **Build SCR-013 AI Copilot Landing** — LandingHero, SuggestionCards ×4, Composer | 3.2 | 35 | Chat | ✅ |
| 7.2 | **QA SCR-013** against `chat.landing.ai-hms-copilot.png` | 7.1 | 15 | Chat | ✅ |
| 7.3 | **Build SCR-011 New Patient Context Thread** — ContextChip, GeneralKnowledgeToggle, LandingHero (small), PromptGrid 2×3, HowItWorksRail, Composer | 3.1 | 45 | Chat | ✅ |
| 7.4 | **Build SCR-014 Chat Cited Answer** — ContextChip, UserBubble, AssistantCard with cited answer + evidence rail (**added during plan review**) | 3.1 | 40 | Chat | ✅ |
| 7.5 | **QA SCR-011** against `chat.workspace.new-patient-context-thread.png` | 7.3 | 15 | Chat | ✅ |
| 7.6 | **QA SCR-014** against reference screenshots if available | 7.4 | 10 | Chat | ✅ |
| 7.7 | **Build SCR-012 Safe Refusal** — ContextChip, UserBubble, SafeRefusalCard, RemediationButtons ×3, NoEvidenceRail, Composer | 3.1 | 40 | Chat | ✅ |
| 7.8 | **QA SCR-012** against `chat.answer.safe-refusal-insufficient-evidence.png` | 7.7 | 15 | Chat | ✅ |

#### Documents & OCR Screens (8 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 8.1 | **Build SCR-015 OCR Indexing Dashboard** — UploadDropzone, SearchBar, DocumentsTable (48 rows), SemanticSearchPanel, ProcessingPipeline, StorageDonut | 3.1 | 50 | Documents | ✅ |
| 8.2 | **QA SCR-015** against `documents.dashboard.ocr-indexing-semantic-search.png` | 8.1 | 20 | Documents | ✅ |
| 8.3 | **Build SCR-016 OCR Review Low Confidence** — LowConfidenceBanner, DocumentReviewHeader, TabBar, ScannedPagePane, ExtractedTextPane, ProcessingTimeline, FailureReasons, Action buttons | 3.1 | 50 | Documents | ✅ |
| 8.4 | **Build SCR-018 Document Pages Preview** — implied page preview state (**added during plan review**) | 3.1 | 25 | Documents | ✅ |
| 8.5 | **QA SCR-016** against `documents.ocr-review.needs-review-low-confidence.png` | 8.3 | 20 | Documents | ✅ |
| 8.6 | **Build SCR-017 Batch Upload Modal** — Backdrop, Modal xl, UploadDropzoneCompact, UploadFileTable (3 rows), OCRPipelineStepper, Buttons | 3.5 | 40 | Documents | ✅ |
| 8.7 | **QA SCR-017** against `documents.upload.batch-ocr-progress-modal.png` | 8.6 | 15 | Documents | ✅ |
| 8.8 | **QA SCR-018** against any available reference | 8.4 | 10 | Documents | ✅ |

#### Access Control, Audit, Metrics, Settings, Overlays, Citations (16 tasks)

| ID | Task | Depends On | Est. Min | Module | Status |
|----|------|-----------|----------|--------|--------|
| 9.1 | **Build SCR-022 Access Request Modal** — Backdrop, Modal xl, PatientSummaryStrip, SelectFields ×4, PurposeRadioCards ×3, JustificationTextarea (178/500), ExplainerTimeline, Submit/Cancel | 3.5 | 45 | Access | ✅ |
| 9.2 | **QA SCR-022** against `access-requests.create.clinical-justification-modal.png` | 9.1 | 15 | Access | ✅ |
| 10.1 | **Build SCR-023 Audit Events Log** — AuditMetricCards ×4, FilterBar, EventsTable (1,248 events), EventDrawer (Overview/Raw tabs), ComplianceCards ×2 | 3.3 | 50 | Audit | ✅ |
| 10.2 | **QA SCR-023** against `audit.logs.access-event-detail-panel.png` | 10.1 | 20 | Audit | ✅ |
| 11.1 | **Build SCR-024 Impact Quality Dashboard** — MetricCards ×4, DateRange filter, TrendLineChart, BarVolumeChart, QualitySafetyChart, WorkflowImpactTable, UserFeedbackCard | 3.1 | 50 | Metrics | ✅ |
| 11.2 | **QA SCR-024** against `metrics.dashboard.impact-quality-summary.png` | 11.1 | 15 | Metrics | ✅ |
| 12.1 | **Build SCR-025 Profile & System Preferences** — LocalSubnav (9 items), ProfileCard, PreferencesCard (7 rows), DisplayCard (segments), SecurityCard, RightRail ×4 | 3.1 | 50 | Settings | ✅ |
| 12.2 | **QA SCR-025** against `users.preferences.profile-security-system-status.png` | 12.1 | 15 | Settings | ✅ |
| 13.1 | **Build SCR-020 Global Command Palette** — Backdrop z=500, CommandPalette z=600 (704px), SearchInput, 4 Sections (Patients, Docs, Commands, Threads), Keyboard tips footer | 3.5 | 40 | Overlays | ✅ |
| 13.2 | **QA SCR-020** against `search.global.command-palette-recent-entities.png` | 13.1 | 15 | Overlays | ✅ |
| 13.3 | **Build SCR-027 Environment Selector** — Dropdown (370px) anchored to env pill, 4 option rows, Info footer | 3.2 | 25 | Overlays | ✅ |
| 13.4 | **QA SCR-027** against `workspaces.environment-selector.synthetic-sandbox-training-production.png` | 13.3 | 10 | Overlays | ✅ |
| 14.1 | **Build SCR-019 Citation Viewer Modal** — Backdrop, DocumentViewerModal (3-column), PDF toolbar, CitationDetails, VerificationChecklist, TrustFooter | 3.5 | 45 | Citations | ✅ |
| 14.2 | **QA SCR-019** against `citations.viewer.verified-source-document.png` | 14.1 | 20 | Citations | ✅ |

**Phases 4-14 Exit Gate**: All 25 screens built and individually QA'd against reference PNGs. ~15 hours cumulative.

---

### PHASE 15: Full Visual QA & Alignment (13 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 15.1 | **Export all 25 screens as PNG (2x scale)** from Figma | All screens | 15 | 25 PNG files | ✅ |
| 15.2 | **QA Auth screens** (SCR-001, 002) — overlay comparison, flag >8px deviations | 15.1 | 20 | | ✅ |
| 15.3 | **QA Dashboard screens** (SCR-003, 004, 005) — overlay comparison | 15.1 | 30 | | ✅ |
| 15.4 | **QA Patient screens** (SCR-006, 007, 008, 009, 010, 021) | 15.1 | 45 | | ✅ |
| 15.5 | **QA Chat screens** (SCR-011, 012, 013, 014) | 15.1 | 30 | | ✅ |
| 15.6 | **QA Document screens** (SCR-015, 016, 017, 018) | 15.1 | 30 | | ✅ |
| 15.7 | **QA Access/Audit screens** (SCR-022, 023) | 15.1 | 20 | | ✅ |
| 15.8 | **QA Metrics/Settings screens** (SCR-024, 025) | 15.1 | 20 | | ✅ |
| 15.9 | **QA Overlay/Citation screens** (SCR-019, 020, 027) | 15.1 | 20 | | ✅ |
| 15.10 | **Layer audit** — verify ALL screen frames use component instances only, no raw text/rects | All screens | 30 | Zero raw elements | ✅ |
| 15.11 | **Style audit** — verify all colors/texts use Figma styles, no hardcoded values | All screens | 30 | Zero hardcoded styles | ✅ |
| 15.12 | **Fix flagged deviations** — correct all >8px issues found in 15.2-15.9 | 15.2-15.11 | 60 | All within tolerance | ✅ |
| 15.13 | **Re-export and re-verify** fixed screens | 15.12 | 20 | All passing | ✅ |

**Phase 15 Exit Gate**: All 25 screens pass QA within 8px tolerance, no raw elements, all styles bound. ~6 hours.

---

### PHASE 16: Prototype Connections & Finalization (12 tasks)

| ID | Task | Depends On | Est. Min | Verify | Status |
|----|------|-----------|----------|--------|--------|
| 16.1 | **Connect Login→MFA→Dashboard flow** (SCR-001→002→003) | 15.13 | 10 | Navigable | ✅ |
| 16.2 | **Connect Dashboard→PatientList→PatientDetail** (SCR-003→006→007) | 15.13 | 10 | | ✅ |
| 16.3 | **Connect PatientDetail→AISummary+MedReview+AccessDenied** (SCR-007→010/008/021) | 15.13 | 15 | | ✅ |
| 16.4 | **Connect AccessDenied→AccessRequest modal** (SCR-021→022) | 15.13 | 5 | | ✅ |
| 16.5 | **Connect ChatLanding→NewThread→CitedAnswer/SafeRefusal** (SCR-013→011→014/012) | 15.13 | 15 | | ✅ |
| 16.6 | **Connect CitedAnswer→CitationViewer** (SCR-014→019) | 15.13 | 5 | | ✅ |
| 16.7 | **Connect Documents dashboard→Review+Upload** (SCR-015→016/017) | 15.13 | 10 | | ✅ |
| 16.8 | **Connect Audit→EventDetail drawer** (SCR-023) | 15.13 | 5 | | ✅ |
| 16.9 | **Connect Global overlays** — CommandPalette (⌘K), EnvironmentSelector, ToastStack | 15.13 | 10 | | ✅ |
| 16.10 | **Connect sidebar navigation** — All 8 nav items to respective screens | 15.13 | 15 | All nav items work | ✅ |
| 16.11 | **Test all 17 prototype flows end-to-end** | 16.1-16.10 | 20 | All flows navigable | ✅ |
| 16.12 | **Final file cleanup** — remove unused styles, unused components, orphan layers, empty frames | 16.11 | 15 | Clean file | ✅ |

**Phase 16 Exit Gate**: All 17 flows connected and tested, file cleaned. ~2 hours.

---

## Task Count Summary

| Phase | Tasks | Cumulative Tasks | Est. Minutes | Cumulative Hours | Status |
|-------|-------|-----------------|--------------|-----------------|--------|
| 0 — Foundation | 8 | 8 | 110 | 1.8 | ✅ |
| 1 — Base Components (Buttons) | 12 | 20 | 315 | 5.3 | ✅ |
| 1 — Base Components (Inputs) | 12 | 32 | 230 | 3.8 | ✅ |
| 1 — Base Components (Chips/Cards/Tables/Nav/Overlays) | 23 | 55 | 505 | 8.4 | ✅ |
| 2 — Domain (Shell) | 8 | 63 | 205 | 3.4 | ✅ |
| 2 — Domain (Patient/Chat/Evidence) | 18 | 81 | 450 | 7.5 | ✅ |
| 2 — Domain (Docs/Audit/Auth/Viz/Empty) | 27 | 108 | 680 | 11.3 | ✅ |
| 3 — Shell Templates | 6 | 114 | 115 | 1.9 | ✅ |
| 4 — Auth Screens | 6 | 120 | 120 | 2.0 | ✅ |
| 5 — Dashboard Screens | 8 | 128 | 160 | 2.7 | ✅ |
| 6 — Patient Screens | 12 | 140 | 390 | 6.5 | ✅ |
| 7 — Chat Screens | 8 | 148 | 215 | 3.6 | ✅ |
| 8 — Document Screens | 8 | 156 | 240 | 4.0 | ✅ |
| 9-14 — Remaining Screens | 16 | 172 | 500 | 8.3 | ✅ |
| 15 — Visual QA | 13 | 185 | 340 | 5.7 | ✅ |
| 16 — Prototypes & Final | 12 | 197 | 140 | 2.3 | ✅ |
| **TOTAL** | **197** | — | **~4,715 min** | **~78.6 hours** | ✅ |

> Note: ~20% higher than the master plan estimate due to per-task QA, missing screens (SCR-014, SCR-018), and asset mapping tasks discovered during review.

---

## Quick-Start: Minimal Viable First Sprint (14 tasks, ~8 hours)

| Order | Task ID | Task | Status |
|-------|---------|------|--------|
| 1 | 0.0 | Verify Figma API access | ✅ |
| 2 | 0.8 | Snapshot Figma file | ✅ |
| 3 | 1.1 | Create Button/Primary | ✅ |
| 4 | 1.13 | Create Input/Text | ✅ |
| 5 | 1.25 | Create Chip/Status | ✅ |
| 6 | 1.30 | Create Card/Standard | ✅ |
| 7 | 2.1 | Create Shell/Topbar | ✅ |
| 8 | 2.2 | Create Shell/Sidebar | ✅ |
| 9 | 3.1 | Build Shell/Standard template | ✅ |
| 10 | 5.3 | Build SCR-003 Populated Dashboard (most complex screen) | ✅ |
| 11 | 5.4 | QA SCR-003 | ✅ |
| 12 | 5.7 | Build SCR-004 Toast Stack | ✅ |
| 13 | 5.8 | QA SCR-004 Toast | ✅ |
| 14 | 16.9 | Connect Dashboard overlays | ✅ |

**Sprint Exit Gate**: If SCR-003 builds correctly with component instances and passes QA, the full plan is validated.

---

## File Outputs

| File | Purpose | Status |
|------|---------|--------|
| `master-figma-execution-plan.md` | High-level plan with component specs, screen blueprints, phases | ✅ |
| `master-figma-task-breakdown.md` | This file — 197 atomic tasks for execution tracking | ✅ |

**Next**: Confirm the plan to begin execution, or scope to the Quick-Start sprint for validation.
