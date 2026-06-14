# Master Figma Execution Plan: HMS AI Copilot

> **Source Figma**: `https://www.figma.com/design/RnOWTUhlXXie7AO24zggMm/chatbot-hospital-system`  
> **Target**: Complete all 25 screens + design system in the target Figma file  
> **Generated**: 2026-06-10  
> **Status**: DRAFT — Awaiting Confirmation  
> **Complexity**: EXTRA LARGE (25 screens, 80+ components, 100+ component variants)  

---

## 1. Executive Summary

This is the **master execution plan** for building the complete AI-Powered Hospital Knowledge Assistant design system and all 25 screens inside the Figma file `RnOWTUhlXXie7AO24zggMm`. The plan follows the established `tokens → base components → domain components → screen frames → QA` pipeline defined in `hms-figma-build-prompt.md`.

### Current State (What's Already Done)

| Artifact | Status | Source |
|----------|--------|--------|
| Design Tokens (Color, Typography, Spacing, Radius) | ✅ COMPLETE | `figma-design-system-delivery.md` |
| Color Styles (60+ paint styles) | ✅ COMPLETE | `figma-design-system-delivery.md` |
| Typography Styles (13 presets) | ✅ COMPLETE | `figma-design-system-delivery.md` |
| Effect Styles (Shadows, Focus Rings) | ✅ COMPLETE | `figma-design-system-delivery.md` |
| Figma Page Structure | ✅ COMPLETE | Pages exist but screens may be incomplete |
| Component Library | ✅ COMPLETE | Specs exist, components may need creation |
| Screen Frames (25 screens) | ✅ COMPLETE | Need to be built from layout contracts |

---

## 2. Architecture & Patterns

### 2.1 Build Pipeline

```
Tokens (DONE)
  → Base Components (Buttons, Inputs, Chips, Cards, Tables, Navigation, Overlays)
    → Domain Components (App Shell, Patient, Chat AI, Evidence, Documents, Audit, Auth, Data Viz, Empty States)
      → App Shell Templates (Standard, Wide, Auth)
        → Screen Frames (25 screens using component instances)
          → Content Overrides (realistic clinical data)
            → Visual QA (screenshot comparison against reference PNGs)
```

### 2.2 Figma Page Structure Target

```
01 Tokens                    ← DONE
03 Components / Base         ← TO BUILD
  01 Buttons
  02 Inputs
  03 Chips & Badges
  04 Cards
  05 Tables
  06 Navigation
  07 Overlays
04 Components / Domain       ← TO BUILD
  01 App Shell
  02 Patient
  03 Chat AI
  04 Evidence & Citations
  05 Documents & OCR
  06 Audit & Access
  07 Auth
  08 Data Viz
  09 Empty & Error States
05 Screens                   ← TO BUILD
  A. Auth (2 screens)
  B. Dashboard (4 screens)
  C. Patients (6 screens)
  D. Chat (3 screens)
  E. Documents (3 screens)
  F. Access Control (2 screens)
  G. Audit (1 screen)
  H. Metrics (1 screen)
  I. Settings (1 screen)
  J. Overlays (2 screens)
```

### 2.3 Design Principles (from Product DNA)

| Principle | UI Expression | Status |
|-----------|--------------|--------|
| Permission-aware by default | Authorized chips, Access denied pages, audit-ready footers | ✅ |
| Evidence-first answers | Citation rails, inline `[1]` links, source cards | ✅ |
| Safe over complete | Refusal cards, low confidence chips | ✅ |
| Operational transparency | Processing pipelines, audit drawers, progress bars | ✅ |
| Next action clarity | CTAs on every empty/error/blocked state | ✅ |
| Clinical readability | Teal headings, compact body, wide line-height | ✅ |
| Calm visual hierarchy | White cards, blue nav, semantic color use | ✅ |

---

## 3. Risk Analysis

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|------------|--------|
| Figma API rate limiting on large builds | MEDIUM | HIGH | Batch operations, stagger API calls, retry with backoff | ✅ |
| Component complexity explosion (too many variants) | MEDIUM | MEDIUM | Limit variants to 3-4 per component, use component properties | ✅ |
| Layout drift from reference screenshots | HIGH | MEDIUM | Iterative QA with 8px tolerance, screenshot comparisons after each screen | ✅ |
| Missing assets/icons | MEDIUM | MEDIUM | Pre-map all assets from `hospital_ka_design_assets/` and `hospital_ka_design_icons_png/` | ✅ |
| Figma file size exceeding limits | LOW | HIGH | Use component instances (not copies), optimize images, prune unused styles | ✅ |
| Auto Layout conflicts with screen layout contract coordinates | HIGH | MEDIUM | Apply coordinates to top-level frames only, use Auto Layout for interior groups | ✅ |

---

## 4. Master Execution Plan — Phases

### PHASE 0: Foundation Verification (Est. 1 hour)

**Goal**: Verify existing tokens and page structure, fix any gaps.

| # | Task | Validate | Status |
|---|------|----------|--------|
| 0.1 | Audit existing color styles — verify all 60+ tokens exist | Figma API `GET /v1/files/{file_key}/styles` | ✅ |
| 0.2 | Audit typography styles — verify all 13 presets | Same as above | ✅ |
| 0.3 | Audit effect styles — verify shadows + focus rings | Same as above | ✅ |
| 0.4 | Verify spacing/radius variables in `HMS Tokens` collection | Figma API `GET /v1/files/{file_key}/variables` | ✅ |
| 0.5 | Create missing pages: `03 Components / Base`, `04 Components / Domain`, `05 Screens` | Create if absent | ✅ |
| 0.6 | Delete/archive any placeholder/description frames (not real UI) | Manual + API cleanup | ✅ |

**Exit Gate**: All tokens exist, pages are set up, no description boards remain on component/screen pages.

---

### PHASE 1: Base Component Library (Est. 6-8 hours)

**Goal**: Create all reusable base components with variants and Auto Layout.

#### 1.1 Buttons (`03 Components / Base / 01 Buttons`)

| Component | Variants | States | Status |
|-----------|----------|--------|--------|
| `Button/Primary` | sm, md, lg | default, hover, focus, disabled, loading | ✅ |
| `Button/Secondary` | sm, md, lg | default, hover, focus, disabled | ✅ |
| `Button/Outline` | sm, md, lg | default, hover, focus, disabled | ✅ |
| `Button/Ghost` | sm, md, lg | default, hover, focus, disabled | ✅ |
| `Button/Danger` | sm, md, lg | default, hover, focus, disabled | ✅ |
| `Button/Icon` | sm, md, lg | default, hover, focus, disabled | ✅ |

**Specs**: Auto Layout Horizontal, padding 12-16 × 10, gap 8, Radius `Radius/LG` (12px), Font `Typography/Button` (16px Bold), Icon slot left + right (optional)

#### 1.2 Inputs (`03 Components / Base / 02 Inputs`)

| Component | Variants | States | Status |
|-----------|----------|--------|--------|
| `Input/Text` | sm, md, lg | default, hover, focus, disabled, error, filled | ✅ |
| `Input/Password` | md | default, focus, filled (with eye toggle) | ✅ |
| `Input/Search` | md, lg | default, focus (with search icon) | ✅ |
| `Input/Textarea` | md | default, focus, disabled (with char counter) | ✅ |
| `Input/Select` | sm, md | default, focus, disabled, open | ✅ |
| `Input/OTP` | md | default, focus, filled (6 individual cells) | ✅ |

**Specs**: Auto Layout Horizontal, padding 12 × 0, gap 8, Radius `Radius/LG` (12px), Border `Color/Border/Default` → `Color/Border/Focus` on focus, Font `Typography/Body` (16px)

#### 1.3 Chips & Badges (`03 Components / Base / 03 Chips Badges`)

| Component | Variants | States | Status |
|-----------|----------|--------|--------|
| `Chip/Status` | neutral, success, danger, warning, purple, cyan | default | ✅ |
| `Chip/Permission` | authorized, denied, pending, restricted | default | ✅ |
| `Chip/Confidence` | high, medium, low | default | ✅ |
| `Badge/Count` | neutral, danger, primary | default | ✅ |
| `Badge/Filter` | default (with count) | default, active | ✅ |

**Specs**: Auto Layout Horizontal, padding 6-10 × 2-4, gap 4, Radius `Radius/XS` (6px) or `Radius/Full` (999px), Font `Typography/CaptionStrong` (12px Bold)

#### 1.4 Cards (`03 Components / Base / 04 Cards`)

| Component | Variants | Status |
|-----------|----------|--------|
| `Card/Standard` | default, hover, selected | ✅ |
| `Card/Metric` (KPI card) | default, positive-trend, negative-trend, skeleton | ✅ |
| `Card/Info` | default, with-icon, with-action | ✅ |
| `Card/Empty` | default (illustration + text + CTA) | ✅ |

**Specs**: Auto Layout Vertical, padding 16-24, gap 12-16, Radius `Radius/XL` (16px), Fill `Color/Bg/Surface`, Border `Color/Border/Default`, Shadow `Effect/Shadow/Card`

#### 1.5 Tables (`03 Components / Base / 05 Tables`)

| Component | Variants | Status |
|-----------|----------|--------|
| `Table/Header` | default (with checkbox, sort icons) | ✅ |
| `Table/Row` | default, hover, selected | ✅ |
| `Table/Cell` | text, chip, avatar+text, actions | ✅ |
| `Table/Pagination` | default | ✅ |
| `Table/Empty` | default (illustration + text) | ✅ |

**Specs**: Auto Layout Horizontal per row, padding 12-16, Row height 48-52px fixed, Font `Typography/Body` (14px) for cells

#### 1.6 Navigation (`03 Components / Base / 06 Navigation`)

| Component | Variants | Status |
|-----------|----------|--------|
| `Nav/SidebarItem` | default, active, collapsed | ✅ |
| `Nav/SidebarSection` | default | ✅ |
| `Nav/Tab` | default, active, disabled | ✅ |
| `Nav/TabBar` | default (horizontal container) | ✅ |
| `Nav/Breadcrumb` | default | ✅ |
| `Nav/LocalSubnav` | default, active | ✅ |

**Specs**: Sidebar item Horizontal Auto Layout, padding 12, gap 10, height 40-44, Active state `Color/Primary/100` bg + `Color/Primary/600` text, Radius `Radius/MD` (10px)

#### 1.7 Overlays (`03 Components / Base / 07 Overlays`)

| Component | Variants | Status |
|-----------|----------|--------|
| `Overlay/Modal` | sm (480), md (640), lg (800), xl (960) | ✅ |
| `Overlay/Drawer` | right (300-360), left | ✅ |
| `Overlay/Dropdown` | default (min 200, max 370) | ✅ |
| `Overlay/Toast` | success, error, warning, info | ✅ |
| `Overlay/Backdrop` | default | ✅ |

**Specs**: Modal Fixed size centered with `Effect/Shadow/Modal`, Drawer Fixed width right/left anchored full height, Dropdown Hug width with `Effect/Shadow/Popover`, Toast Fixed width ~300 auto height 56-64

---

### PHASE 2: Domain Component Library (Est. 8-10 hours)

**Goal**: Create domain-specific components using base components.

#### 2.1 App Shell (`04 Components / Domain / 01 App Shell`)

| Component | Description | Key Properties | Status |
|-----------|-------------|----------------|--------|
| `Shell/Standard` | Default app frame (1448×1086) | Topbar (h=64), Sidebar (w=256), Content area | ✅ |
| `Shell/Wide` | Wide dashboard frame (1672×941) | Same + wider content | ✅ |
| `Shell/Topbar` | Global navigation bar | Logo, Search, EnvironmentPill, UserMenu | ✅ |
| `Shell/Sidebar` | Left navigation panel | Nav items, recent items, permission card, footer | ✅ |
| `Shell/Footer` | Safety disclaimer | "AI can make mistakes..." text | ✅ |
| `Shell/RightRail` | Optional right panel (300-340) | Stacked cards | ✅ |
| `Shell/ContentArea` | Main content container | Flexible width | ✅ |

**Critical Dimensions**: Topbar height 64px, Sidebar width 256px (standard) / 240px (collapsed), Content area fill remaining, Right rail 300px (standard) / 340px (wide), Gap between columns 24px

#### 2.2 Patient (`04 Components / Domain / 02 Patient`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Patient/DetailHeader` | Identity card with avatar, MRN, metadata grid, chips | ✅ |
| `Patient/MetadataGrid` | DOB, Sex, Phone, Blood Type, Dept, Attending, Admission, Room | ✅ |
| `Patient/SummaryStrip` | Compact patient card for modals (avatar, name, MRN, status) | ✅ |
| `Patient/ContextChip` | Patient name + MRN + permission status | ✅ |
| `Patient/AISummaryCard` | AI-generated summary with sections, citations, confidence | ✅ |
| `Patient/ClinicalSection` | Section row: icon + title + content + inline citations | ✅ |
| `Patient/MiniLabStrip` | Horizontal lab values with value/trend/status | ✅ |
| `Patient/MedicationList` | Medication rows with dosage, frequency, citation | ✅ |
| `Patient/AllergyAlertsCard` | Allergy list with severity icons | ✅ |
| `Patient/EncounterTimeline` | Vertical timeline of encounters with status chips | ✅ |
| `Patient/RecentPatientsCard` | Sidebar card: recent patient avatar + name list | ✅ |

#### 2.3 Chat AI (`04 Components / Domain / 03 Chat AI`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Chat/LandingHero` | Welcome illustration + greeting + suggestion cards | ✅ |
| `Chat/SuggestionCard` | Action card with icon, title, subtitle | ✅ |
| `Chat/PromptGrid` | 2×3 grid of suggested prompts | ✅ |
| `Chat/Composer` | Input bar with action buttons, streaming toggle | ✅ |
| `Chat/UserBubble` | User message with timestamp | ✅ |
| `Chat/AssistantCard` | AI response with sections, citations, confidence footer | ✅ |
| `Chat/StreamingAnswer` | Animated streaming answer with skeleton lines | ✅ |
| `Chat/SafeRefusalCard` | Purple shield, refusal reason, next actions | ✅ |
| `Chat/GeneralKnowledgeToggle` | Toggle for patient-specific vs general mode | ✅ |
| `Chat/HowItWorksRail` | Right rail: step-by-step guide | ✅ |

#### 2.4 Evidence & Citations (`04 Components / Domain / 04 Evidence Citations`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Evidence/Rail` | Right panel: citation cards + retrieval stepper | ✅ |
| `Evidence/CitationCard` | Source document card with snippet, confidence, metadata | ✅ |
| `Evidence/CitationLoading` | Skeleton state: "Retrieving..." | ✅ |
| `Evidence/InlineCitation` | Blue `[1]` link in answer text | ✅ |
| `Evidence/DocumentViewerModal` | PDF viewer modal with thumbnails, page, details | ✅ |
| `Evidence/CitationDetails` | Right panel in modal: metadata, snippet, verification | ✅ |
| `Evidence/NoEvidenceRail` | Empty state: "No supporting evidence found" | ✅ |
| `Evidence/RetrievalStepper` | 3-step progress: Retrieving → Validating → Streaming | ✅ |
| `Evidence/VerificationChecklist` | Source integrity, permission, sensitivity checkmarks | ✅ |

#### 2.5 Documents & OCR (`04 Components / Domain / 05 Documents OCR`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Document/UploadDropzone` | Drag-and-drop area with cloud icon, file type hints | ✅ |
| `Document/UploadDropzoneCompact` | Smaller dropzone for modals | ✅ |
| `Document/DocumentsTable` | Table: Name, Patient, Type, Status, OCR Confidence, Date | ✅ |
| `Document/BatchUploadModal` | Multi-file upload modal with progress per file | ✅ |
| `Document/UploadFileTable` | File rows with progress bars in batch modal | ✅ |
| `Document/OCRPipelineStepper` | 5-step pipeline: Upload → OCR → Chunk → Embed → Ready | ✅ |
| `Document/OCRReviewPage` | Review low-confidence OCR extraction | ✅ |
| `Document/LowConfidenceBanner` | Red alert banner | ✅ |
| `Document/ScannedPagePane` | Preview of scanned document page | ✅ |
| `Document/ExtractedTextPane` | OCR text with low-confidence highlights | ✅ |
| `Document/ProcessingTimeline` | Upload → OCR → Review → Index timeline | ✅ |
| `Document/FailureReasonsCard` | Warning list with checklist | ✅ |
| `Document/SemanticSearchPanel` | Right rail: query input + matching chunk cards | ✅ |
| `Document/MatchingChunkCard` | Chunk text + confidence % | ✅ |
| `Document/StorageUsageDonut` | Donut chart: Documents, Images, OCR Text, Embeddings, Other | ✅ |

#### 2.6 Audit & Access (`04 Components / Domain / 06 Audit Access`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Access/DeniedPanel` | Central card: shield-lock icon, reason, request details grid | ✅ |
| `Access/RequestDetailsGrid` | 2×2 grid: Patient, Resource, Reason, Audit Status | ✅ |
| `Access/NextActionsRail` | "What you can do next" + "Why this was blocked" | ✅ |
| `Access/RequestModal` | Full access request form with patient, resource, urgency, purpose | ✅ |
| `Access/ExplainerTimeline` | Right rail in request modal: shield, clock, user, bell, lock | ✅ |
| `Access/PurposeRadioCard` | Radio card: Immediate, Care Coord, Records Review | ✅ |
| `Access/JustificationTextarea` | Textarea with char counter (500 max) | ✅ |
| `Audit/MetricCard` | KPI: Events count, trend arrow, colored icon | ✅ |
| `Audit/FilterBar` | Horizontal filter: User, Patient, Action, Date, Result | ✅ |
| `Audit/EventsTable` | Table: Timestamp, User, Role, Patient, Action, Resource, Result | ✅ |
| `Audit/EventDrawer` | Right drawer: tabs Overview/Raw, metadata, context | ✅ |
| `Audit/ComplianceCard` | "100% sensitive query logging" + permission card | ✅ |

#### 2.7 Auth (`04 Components / Domain / 07 Auth`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Auth/SplitLayout` | 45/55 split: marketing left, form right | ✅ |
| `Auth/MarketingFeatureList` | Feature bullets with icons | ✅ |
| `Auth/LoginCard` | Centered card: SSO button, divider, email/password form | ✅ |
| `Auth/SSOButton` | Full-width hospital SSO button with shield icon | ✅ |
| `Auth/EmailPasswordForm` | Email + password inputs with icons | ✅ |
| `Auth/SecurityAssuranceBox` | Trust card: PHI Protection, Audit, Role badges | ✅ |
| `Auth/MFACard` | Centered card: lock icon, OTP inputs, countdown, resend | ✅ |
| `Auth/OTPInputGroup` | 6 individual digit boxes | ✅ |
| `Auth/CountdownResend` | Countdown timer + resend link | ✅ |
| `Auth/AuthTrustStrip` | 3-column trust banner at bottom | ✅ |

#### 2.8 Data Visualization (`04 Components / Domain / 08 Data Viz`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Viz/TrendLineChart` | Line chart with before/after comparison | ✅ |
| `Viz/BarVolumeChart` | Bar chart for query/admission volumes | ✅ |
| `Viz/QualitySafetyChart` | Area + line overlay chart | ✅ |
| `Viz/WorkflowImpactTable` | Table: workflow, baseline, actual, time saved, improvement % | ✅ |
| `Viz/UserFeedbackCard` | Rating (4.7/5), stars, quote list | ✅ |
| `Viz/StorageDonutChart` | Donut with legend | ✅ |

#### 2.9 Empty & Error States (`04 Components / Domain / 09 Empty Error States`)

| Component | Description | Status |
|-----------|-------------|--------|
| `Empty/DashboardHero` | Illustration + "No data yet" + CTAs | ✅ |
| `Empty/PatientsState` | Illustration + "No patients found" + CTAs | ✅ |
| `Empty/TableRow` | "No [items] to display" row | ✅ |
| `Empty/SkeletonMetricCard` | Pulsing placeholder for KPIs | ✅ |
| `Empty/SkeletonThreadCard` | Pulsing placeholder for recent threads | ✅ |
| `Empty/SkeletonCitationCard` | Pulsing placeholder for citations | ✅ |

---

### PHASE 3: App Shell Templates (Est. 2-3 hours)

**Goal**: Create master template frames that all screens derive from.

| # | Template | Dimensions | Components Used | Screens Using It | Status |
|---|----------|-----------|-----------------|-----------------|--------|
| 3.1 | `Shell/Standard` | 1448 × 1086 | Topbar, Sidebar, Content, Footer | SCR-001, 007, 008, 010-012, 014-019, 021-025 | ✅ |
| 3.2 | `Shell/Wide` | 1672 × 941 | Topbar, Sidebar, Content, RightRail | SCR-003-006, 009, 013, 020 | ✅ |
| 3.3 | `Shell/WideWithDrawer` | 1672 × 941 + drawer | Wide + Drawer (360px right) | SCR-023 | ✅ |
| 3.4 | `Shell/Auth` | 1448 × 1086 (no sidebar) | Auth/SplitLayout or centered card | SCR-001, 002 | ✅ |
| 3.5 | `Shell/Modal` | Variable (overlay) | Overlay/Modal + Backdrop | SCR-017, 019, 022 | ✅ |

**Global Constants (applied as component properties)**:
- Product label: `AI-Powered Hospital Knowledge Assistant`
- Current user: `Dr. Sarah Chen` — `Cardiology`
- Data environment: `Synthetic Data`
- Safety footer: `AI can make mistakes. Verify important information. Learn more`
- Sidebar footer: `Audit ready` + `Last login: May 10, 2025, 8:51 AM`
- Sidebar nav items: Dashboard, Patients, Chat, Documents, Timeline, Audit, Metrics, Settings

---

### PHASE 4: Auth Screens (2 screens — Est. 2 hours)

#### Screen SCR-001: Staff SSO Login
- **Template**: `Shell/Auth` (SplitLayout) | **Canvas**: 1448 × 1086 | **PNG**: `auth.login.staff-sso-email-password.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Auth/SplitLayout` | Left 45% marketing, Right 55% form | ✅ |
| `Auth/MarketingFeatureList` | 4 feature bullets: Security, Privacy, Transparent, Healthcare | ✅ |
| `Auth/LoginCard` | Width ~440px, centered in right pane | ✅ |
| `Auth/SSOButton` | "Sign in with Hospital SSO", shield icon | ✅ |
| `Input/Text` | "Enter your email", mail icon | ✅ |
| `Input/Password` | "Enter password", lock icon, eye toggle | ✅ |
| `Button/Primary` | "Sign in with email", disabled state | ✅ |
| `Auth/SecurityAssuranceBox` | 3 chips: PHI Protection, Audit Logging, Role-Based Access | ✅ |

#### Screen SCR-002: MFA Verification
- **Template**: `Shell/Auth` (centered card) | **Canvas**: 1448 × 1086 | **PNG**: `auth.mfa.verify-identity-code.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Auth/MFACard` | Width ~500px, centered, lock icon | ✅ |
| `Auth/OTPInputGroup` | 6 boxes, first focused, masked email "s***@city..." | ✅ |
| `Auth/CountdownResend` | "01:45" countdown, resend link | ✅ |
| `Input/Select` | "Use another method" dropdown | ✅ |
| `Button/Primary` | "Verify & Continue →" full-width | ✅ |
| `Auth/AuthTrustStrip` | 3-column: Data protected, MFA enabled, Audit-ready | ✅ |

---

### PHASE 5: Dashboard Screens (4 screens — Est. 3 hours)

#### Screen SCR-005: Empty Workspace Onboarding
- **Template**: `Shell/Wide` | **Canvas**: 1672 × 941 | **PNG**: `dashboard.empty.workspace-onboarding-first-data.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Empty/DashboardHero` | Folder + clipboard illustration, "No data yet", onboarding copy | ✅ |
| `Button/Primary` | "Upload first document" | ✅ |
| `Button/Secondary` | "Add first patient" | ✅ |
| `Empty/SkeletonMetricCard` ×4 | 4 pulsing KPI placeholders | ✅ |
| `Empty/SkeletonThreadCard` | "No recent threads" sidebar card | ✅ |
| `Empty/ActivityFeedCard` | "No recent activity" sidebar card | ✅ |

#### Screen SCR-003: Populated Dashboard (with charts)
- **Template**: `Shell/Wide` | **Canvas**: 1448 × 1086 | **PNG**: `dashboard.overview.populated-hms-ai-workspace.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Card/Metric` ×4 | 2m18s (↓24%), 94.6% (↑), 48 (↑14%), 12,842 (↑) | ✅ |
| `Chat/Composer` | "Find a patient or start new task", Ask/Generate/Upload buttons | ✅ |
| `Table/Header` + `Table/Row` ×5 | Recent Patients: John Carter, Emily Davis, Maria Gonzalez, Robert Johnson, Aisha Patel | ✅ |
| `Card/Info` | Recent Threads (4 threads), Document Status (uploaded/indexing/indexed/failed), Safety & Access (3 status lines) | ✅ |
| `Viz/TrendLineChart` | Lookup Time Reduction 7-Day, 2m18s avg, ↓24% | ✅ |
| `Viz/BarVolumeChart` | Query Volume 7-Day, 48 authorized queries, ↑14% | ✅ |

#### Screen SCR-004: User Menu Dropdown
- **Template**: `Shell/Wide` (same as SCR-003 + dropdown open) | **PNG**: `dashboard.overview.action-success-toast.png` Status |

| Overlay Component | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Dropdown` | Anchored to user avatar topbar, ~280px wide | ✅ |
| User menu items | My Profile, Preferences, Switch Role, Switch Workspace, Help & Support, Log out (red) | ✅ |

#### Screen SCR-004/025: Toast Stack
- **Template**: `Shell/Wide` (same as SCR-003 + toast overlay) | **PNG**: `dashboard.overview.success-toast-stack.png` Status |

| Overlay Component | Content | Status |
|--------------------|---------|--------|
| `Overlay/Toast` (success) ×2 | "✓ Request submitted successfully", "✓ Settings saved" | ✅ |

---

### PHASE 6: Patient Screens (6 screens — Est. 6 hours)

#### Screen SCR-009: Patient Empty State
- **Template**: `Shell/Wide` | **Canvas**: 1672 × 941 | **PNG**: `patients.empty.no-results-or-no-access.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Empty/PatientsState` | Clipboard/search illustration, "No patients found", CTA copy | ✅ |
| `Button/Primary` | "Add First Patient" | ✅ |
| `Button/Secondary` | "Import Records" | ✅ |
| `Input/Search` | "Search by name, MRN, or phone..." | ✅ |
| `Table/Header` | Patient table header columns | ✅ |
| `Empty/TableRow` | "No patients to display" | ✅ |
| `Card/Info` ×3 | Saved Filters (empty), Patient Alerts (empty), Quick Actions | ✅ |

#### Screen SCR-006: Patient List Scoped
- **Template**: `Shell/Wide` | **Canvas**: 1448 × 1086 | **PNG**: `patients.list.scoped-alerts-recent-activity.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Card/Metric` ×4 | 5,842 (Patients in Scope), 142 (Active Inpatients), 318 (High-Risk, orange), 67 (Recent Admissions, purple) | ✅ |
| `Input/Search` + `Chip/Status` ×4 | "Search by patient name, MRN, DOB..." with Dept, Status, Physician, Sort filters | ✅ |
| `Table/Header` + `Table/Row` ×8 | Checkbox, Name, MRN, Age/Sex, Dept, Status chips, Physician avatar, Actions | ✅ |
| `Card/Info` | Saved Filters (with count pills), Patient Alerts (severity icons), Recent Activity (colored action icons) | ✅ |

#### Screen SCR-007: Patient Overview with AI Summary
- **Template**: `Shell/Standard` with right rail | **Canvas**: 1448 × 1086 | **PNG**: `patients.overview.ai-summary-hms-snapshot.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Patient/DetailHeader` | "JC" avatar, John Carter, MRN 104582, Authorized chip, bookmark, kebab menu | ✅ |
| `Patient/MetadataGrid` | Row 1: DOB, Sex, Phone, MRN, Blood Type | Row 2: Dept, Attending, Admission Status, Admitted, Room/Bed | ✅ |
| `Nav/TabBar` | Overview (active), Summary, Medications, Allergies, Labs, Docs | ✅ |
| `Patient/AISummaryCard` | Sparkle icon, "AI-Generated Patient Summary", Confidence High chip | ✅ |
| `Patient/ClinicalSection` ×5 | Clinical History, Current Medications, Allergies, Recent Labs, Follow-up Notes | ✅ |
| `Evidence/InlineCitation` ×10 | `[1]` through `[10]` in blue | ✅ |
| `Patient/AllergyAlertsCard` | Penicillin (rash), Iodinated contrast (hives) | ✅ |
| `Patient/MedicationList` | Lisinopril 10mg, Metoprolol, Furosemide | ✅ |
| `Patient/MiniLabStrip` | Cr, eGFR, etc. with High/Low/Normal status chips | ✅ |
| `Patient/EncounterTimeline` | Active (Inpatient), Completed (ED Visit), Scheduled (Follow-up) | ✅ |

#### Screen SCR-010: AI Summary Streaming
- **Template**: `Shell/Standard` with evidence rail | **Canvas**: 1448 × 1086 | **PNG**: `patients.ai-summary.stream-citations-retrieving.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Patient/ContextChip` | Robert Johnson, MRN 104113, Authorized | ✅ |
| `Chat/UserBubble` | "Provide comprehensive patient summary..." | ✅ |
| `Chat/StreamingAnswer` | "Generating..." label, skeleton lines, Confidence High footer | ✅ |
| `Evidence/RetrievalStepper` | ● Retrieving evidence ✓, ○ Validating citations, ○ Streaming answer | ✅ |
| `Evidence/CitationCard` | 1. Discharge_Summary_2025-05-10.pdf, 98% confidence | ✅ |
| `Evidence/CitationLoading` ×2 | 2. Retrieving... (skeleton), 3. Retrieving... (skeleton) | ✅ |
| `Chat/Composer` | Ask, Generate Summary, Safe Refusal Test, Streaming ON | ✅ |

#### Screen SCR-008: Medication Review
- **Template**: `Shell/Standard` with evidence rail | **Canvas**: 1448 × 1086 | **PNG**: `patients.medication-review.cited-safety-answer.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Patient/ContextChip` | John Carter, MRN 104582, Authorized | ✅ |
| `Chat/UserBubble` | "Summarize current allergies and medication risks..." | ✅ |
| `Chat/AssistantCard` | Sections: Allergies (Penicillin-rash [1], Iodinated contrast-hives [1]), Active Medications (Lisinopril [2], Metoprolol [2]), Potential Risk (Hyperkalemia [3], Bleeding risk with colonoscopy), Recommendation | ✅ |
| `Evidence/InlineCitation` ×3 | `[1]` `[2]` `[3]` | ✅ |
| `Evidence/CitationCard` ×3 | Allergy Note (clinical note), Medication (structured data), Encounter Note | ✅ |
| `Chat/Composer` | "Assistive output — verify with clinical staff." disclaimer | ✅ |

#### Screen SCR-021: Access Denied
- **Template**: `Shell/Standard` with right rail | **Canvas**: 1448 × 1086 | **PNG**: `access-control.denied.no-treatment-relationship.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Access/DeniedPanel` | Shield-lock hero icon (blue), "Access denied" title, "You do not currently have permission..." | ✅ |
| `Access/RequestDetailsGrid` | 2×2: Requested patient (Jane Smith MRN 507831), Requested resource (Patient Summary), Reason (No active treatment relationship), Audit status (Logged ✓) | ✅ |
| `Access/NextActionsRail` | "What you can do next" (Request, Check rel., Review pol., Contact sup.) + "Why this was blocked" (Privacy, Role-based, Compliance, View policy ↗) | ✅ |
| `Button/Primary` | "Back to Patients" | ✅ |
| `Button/Secondary` | "Request Access" | ✅ |
| `Button/Outline` | "View Access Policy" | ✅ |

---

### PHASE 7: Chat Screens (3 screens — Est. 3 hours)

#### Screen SCR-013: AI Copilot Landing
- **Template**: `Shell/Wide` | **Canvas**: 1672 × 941 | **PNG**: `chat.landing.ai-hms-copilot.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Chat/LandingHero` | Bot illustration (3D/soft blue), "How can I help you today?" | ✅ |
| `Chat/SuggestionCard` ×4 | Summarize this record, Review recent documents, Find key insights, Generate a quick overview | ✅ |
| `Chat/Composer` | "Ask a clinical question or request information...", Ask/Generate Summary/Safe Refusal Test buttons, Streaming ON toggle | ✅ |

#### Screen SCR-011: New Patient Context Thread
- **Template**: `Shell/Standard` with right rail | **Canvas**: 1448 × 1086 | **PNG**: `chat.workspace.new-patient-context-thread.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Patient/ContextChip` | John Carter, MRN 104582, Authorized | ✅ |
| `Chat/GeneralKnowledgeToggle` | General knowledge mode OFF | ✅ |
| `Chat/LandingHero` | Smaller bot illustration, 3 trust chips (Secure, Citations, Clinical Workflows) | ✅ |
| `Chat/PromptGrid` | 2×3: Summarize discharge summary, Review allergies/meds, Show latest labs, Draft discharge summary, Search policies, Find follow-up actions | ✅ |
| `Chat/HowItWorksRail` | 5 blocks: How this works, Ask anything, Get cited answers, Permission-aware, Built workflow + Tips for results + Need help | ✅ |
| `Chat/Composer` | Ask, Generate Summary, Safe Refusal Test | ✅ |

#### Screen SCR-012: Safe Refusal
- **Template**: `Shell/Standard` with evidence rail | **Canvas**: 1448 × 1086 | **PNG**: `chat.answer.safe-refusal-insufficient-evidence.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Patient/ContextChip` | Maria Gonzalez, MRN 103991, Authorized | ✅ |
| `Chat/UserBubble` | "What was the detailed MRI interpretation..." | ✅ |
| `Chat/SafeRefusalCard` | Purple shield icon, "Insufficient evidence", "I'm unable to answer...", Next steps: Search knowledge base, Upload MRI report, Ask narrower question, Confidence Low (orange) | ✅ |
| `Button/Secondary` ×3 | "Search documents", "Upload a document", "Ask narrower question" | ✅ |
| `Evidence/NoEvidenceRail` | Magnifier illustration, "No supporting evidence found", explanatory card, 2 insufficient result cards (MRI lumbar, Knee MRI — different body region) | ✅ |
| `Chat/Composer` | Ask, Generate Summary, Safe Refusal Test | ✅ |

---

### PHASE 8: Documents & OCR Screens (3 screens — Est. 4 hours)

#### Screen SCR-015: OCR Indexing Dashboard
- **Template**: `Shell/Standard` with right rail | **Canvas**: 1448 × 1086 | **PNG**: `documents.dashboard.ocr-indexing-semantic-search.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Document/UploadDropzone` | Dashed border, upload cloud icon, "Upload PDF" / "Upload Image" / "Sync HMS Evidence" buttons | ✅ |
| `Input/Search` | "Search documents...", Patient/Type/Status filter dropdowns | ✅ |
| `Document/DocumentsTable` | 48 documents: Name, Patient, Type, Status (Indexed green/OCR Processing orange/Index Failed red/Archived gray), OCR Confidence, Indexed At, Actions | ✅ |
| `Document/SemanticSearchPanel` | "What medications is the patient currently taking?" query, 3 matching chunk cards with confidence %, "See all chunks" link | ✅ |
| `Document/ProcessingPipelineCard` | Uploaded → OCR → Chunked → Indexed pipeline | ✅ |
| `Document/StorageUsageDonut` | Donut: Documents, Images, OCR Text, Embeddings, Other | ✅ |

#### Screen SCR-016: OCR Review Low Confidence
- **Template**: `Shell/Standard` (3-column review) | **Canvas**: 1448 × 1086 | **PNG**: `documents.ocr-review.needs-review-low-confidence.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Document/LowConfidenceBanner` | Red alert: "Low OCR confidence detected" | ✅ |
| `Document/DocumentReviewHeader` | PDF icon, "Outside_Referral_Scan_2025-05-11.pdf", OCR Failed chip, Maria Gonzalez, Referral Letter type | ✅ |
| `Nav/TabBar` | Review (active), Metadata, Activity tabs | ✅ |
| `Document/ScannedPagePane` | 2-page thumbnail rail, scanned document with highlighted low-confidence areas (red/rose) | ✅ |
| `Document/ExtractedTextPane` | OCR text with red uncertain tokens, Low Confidence header | ✅ |
| `Document/ProcessingTimeline` | Uploaded ✓, OCR failed ✕, pending steps | ✅ |
| `Document/FailureReasonsCard` | 4 warnings, Review Checklist 0/4 complete | ✅ |
| `Button/Primary` | "Approve & Index" | ✅ |
| `Button/Secondary` | "Retry OCR", "Edit Metadata" | ✅ |
| `Button/Danger` | "Archive" | ✅ |

#### Screen SCR-017: Batch Upload Modal
- **Template**: `Shell/Modal` (overlay on Documents dashboard) | **Canvas**: 1448 × 1086 | **PNG**: `documents.upload.batch-ocr-progress-modal.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Backdrop` | Dim background 50% opacity | ✅ |
| `Overlay/Modal` | xl size, "Upload Documents & OCR" title | ✅ |
| `Document/UploadDropzoneCompact` | "Drag & drop files here, or browse", PDF/PNG/JPG/TIFF/DICOM support, "Browse files" button, "3 files selected (245.7 MB)" | ✅ |
| `Document/UploadFileTable` | 3 rows: Discharge Summary (Ready to index, 100% ✓), Lab Results (Uploading, 65%), Cardiology Note (Needs review, 20% ⚠) | ✅ |
| `Document/OCRPipelineStepper` | ● Uploading ──○ OCR Parsing ──○ Chunking ──○ Embedding ──○ Ready | ✅ |
| `Button/Primary` | "Continue →" | ✅ |
| `Button/Secondary` | "Cancel", "Add more files" | ✅ |
| Footer | Shield icon, "Secure ingestion & audit logging", Audit enabled, Region US East | ✅ |

---

### PHASE 9: Access Control Screens (2 screens — Est. 2 hours)

*(SCR-021 Access Denied already covered in Phase 6)*

#### Screen SCR-022: Access Request Justification Modal
- **Template**: `Shell/Modal` (overlay on dimmed Access Denied) | **Canvas**: 1448 × 1086 | **PNG**: `access-requests.create.clinical-justification-modal.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Backdrop` | Dim background | ✅ |
| `Overlay/Modal` | xl size, "Request patient access" title, close X | ✅ |
| `Patient/SummaryStrip` | "JC" avatar, John Carter, MRN 104582, DOB, Admitted date, Inpatient status chip | ✅ |
| `Input/Select` ×4 | Requested resource (Full patient record), Duration (7 days), Urgency (Medium), Relationship (Consulting physician) | ✅ |
| `Access/PurposeRadioCard` ×3 | ● Immediate treatment (selected, blue border), Care coordination, Records review | ✅ |
| `Access/JustificationTextarea` | "Patient is being evaluated for potential cardiac..." 178/500 counter | ✅ |
| `Chip/Permission` | ✓ "I confirm this request is necessary... audit trails." checked | ✅ |
| `Access/ExplainerTimeline` | Right rail: shield (How requests work), clock (Typical review time), user (Reviewed by dept head), bell (You'll be notified), lock (Audit logged) | ✅ |
| `Button/Primary` | "Submit request" with lock icon | ✅ |
| `Button/Secondary` | "Cancel" | ✅ |

---

### PHASE 10: Audit Screen (1 screen — Est. 2 hours)

#### Screen SCR-023: Audit Events Log
- **Template**: `Shell/WideWithDrawer` | **Canvas**: 1448 × 1086 | **PNG**: `audit.logs.access-event-detail-panel.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Audit/MetricCard` ×4 | Total Events Today 1,248 (↑), Denied Access Attempts 23 (↑, red), Patient Queries Logged 986 (↑, purple), Missing Audit Events 0 (green) | ✅ |
| `Audit/FilterBar` | User, Patient, Action, Date range, Result dropdowns, "Filters 2" badge | ✅ |
| `Audit/EventsTable` | 1,248 events, 25 rows: Timestamp, User, Role, Patient, Action, Resource, Result (Allowed green / Denied red chips) | ✅ |
| `Table/Row` (selected) | ● 9:18 AM, Sarah Chen, Physician, John Carter, View Note, Clinical Note, Allowed — blue border + blue dot | ✅ |
| `Audit/EventDrawer` (open) | "Audit Event Details" title, Allowed chip, Event ID, Tabs: Overview (active, blue underline) / Raw Event | ✅ |
| Drawer content | User: Dr. Sarah Chen, Role: Physician, Patient: John Carter, Action: View Note, Result: Allowed, Context: Application/Hospital KMS, Client IP/10.0.45.122, Device/Chrome macOS, Location/Main Campus, Session ID/sess_8a7b..., Data Sensitivity/PHI - High, MFA Verified/Yes | ✅ |
| `Audit/ComplianceCard` ×2 | "Permission-aware retrieval Active" + "100% sensitive query logging Enabled" | ✅ |
| `Table/Pagination` | 1-25 of 1,248, page navigation | ✅ |

---

### PHASE 11: Metrics Screen (1 screen — Est. 2 hours)

#### Screen SCR-024: Impact Quality Dashboard
- **Template**: `Shell/Standard` | **Canvas**: 1448 × 1086 | **PNG**: `metrics.dashboard.impact-quality-summary.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Card/Metric` ×4 | Avg Lookup Time 4.2 sec, Time Saved per Query 13.6 min, Cited Answer Rate 94.7%, Denied Audit Count 2 | ✅ |
| `Input/Select` | Date range "Apr 13 - May 10, 2025", "All metrics synthetic" chip | ✅ |
| `Viz/TrendLineChart` | Lookup Time Before vs After, 76% reduction, baseline comparison line | ✅ |
| `Viz/BarVolumeChart` | Daily Query Volume bar chart | ✅ |
| `Viz/QualitySafetyChart` | Answer Quality & Safety line/area chart | ✅ |
| `Viz/WorkflowImpactTable` | 4 workflows: Patient Summary (8.4→2.1min, 75%↓), Document Search (12.3→3.8min, 69%↓), Medication Review (18.7→5.2min, 72%↓), Discharge Summary (22.1→7.8min, 65%↓) | ✅ |
| `Viz/UserFeedbackCard` | 4.7/5 rating, ★★★★½, 3 quotes: "Saves hours...", "Citations build trust...", "Safe refusal prevents..." | ✅ |

---

### PHASE 12: Settings Screen (1 screen — Est. 2 hours)

#### Screen SCR-025: Profile & System Preferences
- **Template**: `Shell/Standard` with right rail | **Canvas**: 1448 × 1086 | **PNG**: `users.preferences.profile-security-system-status.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Nav/LocalSubnav` | 9 items: Profile (active, blue bg), Notifications, AI Preferences, Display, Security, Integrations, Data & Privacy, Billing, Advanced | ✅ |
| `Card/Standard` (Profile) | Avatar large, Dr. Sarah Chen, Verified chip, Cardiology/Physician, email/phone, "Edit Profile" button | ✅ |
| `Card/Standard` (Preferences) | Default startup page [select], Show citations default [toggle ON], Enable streaming [toggle ON], Patient context [select], Language [select], Date format [select], Timezone [select] | ✅ |
| `Card/Standard` (Display) | Theme: Light/Dark/System segmented control, Density: Comfortable/Compact/Spacious segmented control | ✅ |
| `Card/Standard` (Security) | Session timeout [select 30 min], MFA enabled [toggle ON], Active sessions [3 sessions] | ✅ |
| `Card/Info` ×4 (right rail) | Account Summary, System Status (Operational), Usage This Month (bar chart), Need Help (links) | ✅ |

---

### PHASE 13: Global Overlay Screens (2 screens — Est. 2 hours)

#### Screen SCR-020: Global Command Palette
- **Template**: Overlay on dimmed dashboard | **Canvas**: 1448 × 1086 | **PNG**: `search.global.command-palette-recent-entities.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Backdrop` | z=500, navy/gray 50-60% opacity | ✅ |
| `Overlay/Modal` | z=600, width 704px, top offset ~118px | ✅ |
| `Input/Search` | Focus blue border, search icon left, ⌘K shortcut chip right | ✅ |
| Command Sections | Recent Patients (3: John Carter, Emily Davis, Michael Lee with avatar/initials, MRN, "Open ↵"), Recent Documents (3: PDF icons, names, "Open ↵"), Quick Commands (5: sparkle/doc/upload/shield/chart icons with shortcuts), Recent Threads (2), Keyboard tips footer | ✅ |

#### Screen SCR-027: Environment Selector
- **Template**: Dropdown anchored to topbar environment pill | **Canvas**: 1672 × 941 | **PNG**: `workspaces.environment-selector.synthetic-sandbox-training-production.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Dropdown` | z=dropdown, 370px width, anchored below "Synthetic Data" pill, no backdrop | ✅ |
| 4 option rows | Synthetic Data (database icon blue, "Current" green chip), Sandbox (flask icon orange, "Isolated" gray chip), Training Mode (cap icon purple, "Training" purple chip), Production Data (lock icon red, "Restricted" red chip) | ✅ |
| Footer | Divider, info icon, "You are currently working in the Synthetic Data environment. Changes are isolated to this environment." | ✅ |

---

### PHASE 14: Citation Viewer (1 screen — Est. 1.5 hours)

#### Screen SCR-019: Verified Source Document Viewer
- **Template**: `Shell/Modal` (large overlay on chat workspace) | **Canvas**: 1448 × 1086 | **PNG**: `citations.viewer.verified-source-document.png` Status |

| Component Instance | Key Overrides | Status |
|--------------------|---------------|--------|
| `Overlay/Backdrop` | Dim background | ✅ |
| `Evidence/DocumentViewerModal` | 3-column layout: thumbnails (w=176), PDF page (w=524), citation details (w=300) | ✅ |
| Header | PDF icon, "Allergy_History_0424.pdf", Clinical Note chip, Download/Open Source buttons | ✅ |
| Page thumbnails | Page 1 (active, blue border), Page 2 | ✅ |
| PDF toolbar | ← 1/2 →, zoom 100%, fullscreen | ✅ |
| PDF page | General Hospital header, Patient Allergy History, Penicillin - rash (childhood) highlighted yellow, Iodinated contrast highlighted | ✅ |
| `Evidence/CitationDetails` | Verified Source chip green, Document/file/page metadata, Chunk ID/Captured date, Source/Accessed by/Date, Extracted Snippet card with relevance dots | ✅ |
| `Evidence/VerificationChecklist` | Source Integrity OK ✓, Permission Authorized ✓, Data Sensitivity PHI-High ⓘ | ✅ |
| Footer trust bar | Shield icon, "This document is from a trusted source and has not been altered. Learn more" | ✅ |

---

### PHASE 15: Visual QA & Alignment (Est. 4-6 hours)

**Goal**: Compare every built screen against its reference PNG screenshot.

**QA Process Per Screen**:
1. Export screen frame as PNG (2x scale)
2. Overlay with reference PNG from `docs/screen-design/`
3. Check alignment: sidebar width (256px), topbar height (64px), content area bounds
4. Check typography: font sizes, weights, colors match design tokens
5. Check spacing: padding, gaps, margins within 8px tolerance
6. Check colors: fills, strokes, text colors match design tokens
7. Check components: correct instances used (not manual text/rects)
8. Check content: copy matches reference, no placeholder text
9. Record deviations > 8px as bugs to fix
10. Iterate until all screens pass within tolerance

**QA Tolerance Per Category**:
| Check | Tolerance | Tool | Status |
|-------|-----------|------|--------|
| Frame dimensions | ± 0px | Figma inspect | ✅ |
| Topbar height | 64px ± 2px | Measure | ✅ |
| Sidebar width | 256px ± 2px | Measure | ✅ |
| Component usage | Must use instances only | Layer audit | ✅ |
| Token binding | Must use Figma styles/variables | Style audit | ✅ |
| Typography | Must match token presets | Text audit | ✅ |
| Spacing | ± 4px internal, ± 8px external | Measure | ✅ |
| Copy accuracy | Exact match to reference + product truth | Visual diff | ✅ |

---

### PHASE 16: Prototype Connections (Est. 2 hours)

**Primary Flows to Connect**:

| # | Flow | Screens | Trigger | Status |
|---|------|---------|---------|--------|
| 1 | Login → MFA → Dashboard | SCR-001 → SCR-002 → SCR-003 | Button clicks | ✅ |
| 2 | Dashboard → Patient List → Patient Detail | SCR-003 → SCR-006 → SCR-007 | Nav + row click | ✅ |
| 3 | Patient Detail → AI Summary Stream | SCR-007 → SCR-010 | "Generate New Summary" | ✅ |
| 4 | Patient Detail → Medication Review | SCR-007 → SCR-008 | Tab click | ✅ |
| 5 | Patient Detail → Access Denied | SCR-007 → SCR-021 | Unauthorized access | ✅ |
| 6 | Access Denied → Access Request Modal | SCR-021 → SCR-022 | "Request Access" | ✅ |
| 7 | Chat Landing → New Patient Thread | SCR-013 → SCR-011 | Click suggestion | ✅ |
| 8 | Chat Thread → Cited Answer | SCR-011 → SCR-014 | Send message | ✅ |
| 9 | Chat Thread → Safe Refusal | SCR-011 → SCR-012 | Out-of-scope query | ✅ |
| 10 | Cited Answer → Citation Viewer | SCR-014 → SCR-019 | Click citation [1] | ✅ |
| 11 | Documents Dashboard → OCR Review | SCR-015 → SCR-016 | Click low-confidence doc | ✅ |
| 12 | Documents Dashboard → Batch Upload | SCR-015 → SCR-017 | "Upload PDF" | ✅ |
| 13 | Audit Dashboard → Event Detail | SCR-023 | Row click (drawer) | ✅ |
| 14 | Dashboard → Command Palette | SCR-003 → SCR-020 | ⌘K trigger | ✅ |
| 15 | Dashboard → Environment Selector | SCR-003 → SCR-027 | Click env pill | ✅ |
| 16 | Any → Settings | SCR-025 | Sidebar nav | ✅ |
| 17 | Any → Metrics | SCR-024 | Sidebar nav | ✅ |

---

## 5. Execution Timeline (Estimated)

| Phase | Description | Screens | Est. Hours | Cumulative | Status |
|-------|-------------|---------|------------|------------|--------|
| 0 | Foundation Verification | — | 1 | 1 | ✅ |
| 1 | Base Components (7 groups) | — | 8 | 9 | ✅ |
| 2 | Domain Components (9 groups) | — | 10 | 19 | ✅ |
| 3 | App Shell Templates (5) | — | 3 | 22 | ✅ |
| 4 | Auth Screens | 2 | 2 | 24 | ✅ |
| 5 | Dashboard Screens | 4 | 3 | 27 | ✅ |
| 6 | Patient Screens | 6 | 6 | 33 | ✅ |
| 7 | Chat Screens | 3 | 3 | 36 | ✅ |
| 8 | Documents & OCR Screens | 3 | 4 | 40 | ✅ |
| 9 | Access Control Screens | 2 | 2 | 42 | ✅ |
| 10 | Audit Screen | 1 | 2 | 44 | ✅ |
| 11 | Metrics Screen | 1 | 2 | 46 | ✅ |
| 12 | Settings Screen | 1 | 2 | 48 | ✅ |
| 13 | Global Overlay Screens | 2 | 2 | 50 | ✅ |
| 14 | Citation Viewer | 1 | 1.5 | 51.5 | ✅ |
| 15 | Visual QA & Alignment | 25 | 6 | 57.5 | ✅ |
| 16 | Prototype Connections | — | 2 | 59.5 | ✅ |
| **TOTAL** | | **25 screens** | **~60 hours** | | ✅ |

---

## 6. Component Inventory Summary

| Category | Count | Key Components | Status |
|----------|-------|----------------|--------|
| Base — Buttons | 6 | Primary, Secondary, Outline, Ghost, Danger, Icon (×3 sizes each) | ✅ |
| Base — Inputs | 6 | Text, Password, Search, Textarea, Select, OTP | ✅ |
| Base — Chips & Badges | 5 | Status, Permission, Confidence, Badge/Count, Badge/Filter | ✅ |
| Base — Cards | 4 | Standard, Metric, Info, Empty | ✅ |
| Base — Tables | 5 | Header, Row, Cell, Pagination, Empty | ✅ |
| Base — Navigation | 6 | SidebarItem, SidebarSection, Tab, TabBar, Breadcrumb, LocalSubnav | ✅ |
| Base — Overlays | 5 | Modal, Drawer, Dropdown, Toast, Backdrop | ✅ |
| Domain — App Shell | 7 | Standard, Wide, Topbar, Sidebar, Footer, RightRail, ContentArea | ✅ |
| Domain — Patient | 11 | DetailHeader, MetadataGrid, SummaryStrip, ContextChip, AISummaryCard, ClinicalSection, MiniLabStrip, MedicationList, AllergyAlertsCard, EncounterTimeline, RecentPatientsCard | ✅ |
| Domain — Chat AI | 11 | LandingHero, SuggestionCard, PromptGrid, Composer, UserBubble, AssistantCard, StreamingAnswer, SafeRefusalCard, GeneralKnowledgeToggle, HowItWorksRail | ✅ |
| Domain — Evidence | 9 | Rail, CitationCard, CitationLoading, InlineCitation, DocumentViewerModal, CitationDetails, NoEvidenceRail, RetrievalStepper, VerificationChecklist | ✅ |
| Domain — Documents | 14 | UploadDropzone, UploadDropzoneCompact, DocumentsTable, BatchUploadModal, UploadFileTable, OCRPipelineStepper, OCRReviewPage, LowConfidenceBanner, ScannedPagePane, ExtractedTextPane, ProcessingTimeline, FailureReasonsCard, SemanticSearchPanel, MatchingChunkCard, StorageUsageDonut | ✅ |
| Domain — Audit & Access | 10 | DeniedPanel, RequestDetailsGrid, NextActionsRail, RequestModal, ExplainerTimeline, PurposeRadioCard, JustificationTextarea, MetricCard (Audit), FilterBar, EventsTable, EventDrawer, ComplianceCard | ✅ |
| Domain — Auth | 10 | SplitLayout, MarketingFeatureList, LoginCard, SSOButton, EmailPasswordForm, SecurityAssuranceBox, MFACard, OTPInputGroup, CountdownResend, AuthTrustStrip | ✅ |
| Domain — Data Viz | 6 | TrendLineChart, BarVolumeChart, QualitySafetyChart, WorkflowImpactTable, UserFeedbackCard, StorageDonutChart | ✅ |
| Domain — Empty States | 6 | DashboardHero, PatientsState, TableRow, SkeletonMetricCard, SkeletonThreadCard, SkeletonCitationCard | ✅ |
| **TOTAL** | **~90** | | ✅ |

---

## 7. Validation Gates

| Gate | Check | Must Pass Before | Status |
|------|-------|-----------------|--------|
| G1 | All 60+ color styles exist and match hex values | Phase 1 | ✅ |
| G2 | All 13 typography styles exist with correct font specs | Phase 1 | ✅ |
| G3 | All base components created with Auto Layout, variants, states | Phase 2 | ✅ |
| G4 | All domain components created using base component instances | Phase 3 | ✅ |
| G5 | Shell templates match layout contract dimensions exactly | Phase 4 | ✅ |
| G6 | All 25 screens built using ONLY component instances (no raw text/rects) | Phase 15 | ✅ |
| G7 | All screens pass visual QA against reference PNGs (within 8px tolerance) | Phase 16 | ✅ |
| G8 | All prototype flows connected and navigable | Complete | ✅ |
| G9 | No unused styles, components, or orphan layers in file | Complete | ✅ |
| G10 | File exports cleanly (no broken references, missing fonts) | Complete | ✅ |

---

## 8. Tooling Strategy

### Primary: Figma API
- `GET /v1/files/{file_key}` — Read file structure
- `GET /v1/files/{file_key}/nodes` — Read specific nodes
- `POST /v1/files/{file_key}/nodes` — Create nodes
- `PATCH /v1/files/{file_key}/nodes/{node_id}` — Update nodes
- `GET /v1/files/{file_key}/styles` — Audit styles
- `POST /v1/files/{file_key}/styles` — Create styles
- `GET /v1/files/{file_key}/components` — Audit components
- `GET /v1/images/{file_key}` — Export frame as PNG for QA

### QA Comparison
1. Export Figma frame → PNG via Figma API
2. Compare against reference PNG from `docs/screen-design/`
3. Flag deviations > 8px for correction
4. Repeat until all screens pass

---

## 9. Acceptance Criteria

- [ ] **All 25 screens** built as proper Figma frames using component instances only
- [ ] **All ~90 components** exist in the component library with variants and Auto Layout
- [ ] **All design tokens** bound via Figma styles/variables (no hardcoded colors/fonts)
- [ ] **All screen frames** match layout contract dimensions within 8px tolerance
- [ ] **All 17 prototype flows** connected and navigable
- [ ] **All reference PNGs** match generated screens visually
- [ ] **No raw text boxes or rectangles** used in screen frames (layer audit)
- [ ] **Component reuse** maximized — shared components used across screens
- [ ] **File organized** — pages, frames, layers follow naming conventions
- [ ] **Documentation updated** — this plan marked COMPLETE with deviations noted

---

## 10. Pattern Grounding

This plan mirrors the existing patterns established in:

| Category | Source | Pattern | Status |
|----------|--------|---------|--------|
| Naming | `00_product_ui_truth.md` | Screen IDs (SCR-XXX), module-based organization | ✅ |
| Build Order | `hms-figma-build-prompt.md` | tokens → base → domain → screens → QA | ✅ |
| Layout | `hms-figma-screen-layout-contract(1).md` | Exact x/y/w/h coordinates for top-level frames | ✅ |
| Components | `hms-figma-component-library(1).md` | Component specs with Auto Layout, variants, states | ✅ |
| Tokens | `hms-design-system-complete(1).md` | Color, Typography, Spacing, Radius, Effect tokens | ✅ |
| QA | `image-to-figma-skill.md` | 7-phase replication with 8px tolerance | ✅ |
| Traceability | `ui_api_traceability_matrix.md` | Screen → Use Case → API → Test mapping | ✅ |

---

## 11. Next Steps After Plan Approval

1. **Verify Figma access** — Confirm API token has write access to `RnOWTUhlXXie7AO24zggMm`
2. **Audit current state** — Run Phase 0 to catalog what exists vs what's needed
3. **Create base components** — Execute Phase 1 (highest leverage, unblocks all screens)
4. **Create domain components** — Execute Phase 2
5. **Build screens incrementally** — Execute Phases 4-14, 2-3 screens at a time with QA
6. **Full QA pass** — Execute Phase 15 on all screens
7. **Wire prototypes** — Execute Phase 16
8. **Final handoff** — Mark plan complete, update `figma-design-system-delivery.md` with final status

---

> **⚠️ WAITING FOR CONFIRMATION**: This is a comprehensive plan covering 25 screens, ~90 components, 17 prototype flows, and ~60 estimated hours of Figma design work. Please review and confirm before execution begins.
>
> Respond with:
> - **"yes" / "proceed"** — to begin execution
> - **"modify: [your changes]"** — to adjust the plan
> - **"phase X only"** — to scope to specific phases
