# figma-screen-layout-contract.md — Pixel Layout Contracts

> Mục tiêu: file này bổ sung phần Figma bị thiếu: **x/y/w/h, grid, Auto Layout, z-index, anchor, component tree** cho từng màn hình.  
> Các giá trị được đo/ước lượng từ PNG đã cung cấp và dùng như contract dựng Figma. Khi cần pixel-perfect, đối chiếu lại ảnh ở 100% zoom và tinh chỉnh ±4 px.

---

## 0. Global Geometry Tokens

### 0.1 Standard App Shell — 1448 × 1086

```yaml
Frame: 1448x1086
Sidebar:
  x: 0
  y: 0
  w: 244
  h: 1086
Topbar:
  x: 244
  y: 0
  w: 1204
  h: 84
Content:
  x: 244
  y: 84
  w: 1204
  h: 1002
ContentPadding:
  x: 24
  y: 24
DefaultGap: 16
FooterDisclaimer:
  y: 1050
  align: center
```

### 0.2 Wide App Shell — 1672 × 941

```yaml
Frame: 1672x941
Sidebar:
  x: 0
  y: 0
  w: 288
  h: 941
Topbar:
  x: 288
  y: 0
  w: 1384
  h: 84
Content:
  x: 288
  y: 84
  w: 1384
  h: 857
ContentPadding:
  x: 28
  y: 24
DefaultGap: 20
FooterDisclaimer:
  y: 910
  align: center
```

### 0.3 Topbar anchor points

```yaml
StandardTopbar:
  Search: {x: 362, y: 16, w: 590, h: 50}
  EnvironmentPill: {x: 990, y: 21, w: 170, h: 44}
  ShieldIcon: {x: 1180, y: 29, w: 28, h: 28}
  UserTrigger: {x: 1220, y: 16, w: 190, h: 52}

WideTopbar:
  Search: {x: 420, y: 16, w: 640, h: 50}
  EnvironmentPill: {x: 1185, y: 21, w: 170, h: 44}
  ShieldIcon: {x: 1370, y: 29, w: 28, h: 28}
  UserTrigger: {x: 1410, y: 16, w: 220, h: 52}
```

### 0.4 z-index

```yaml
z.base: 0
z.sidebar: 10
z.topbar: 20
z.rail: 30
z.dropdown: 200
z.drawer: 250
z.backdrop: 500
z.modal: 600
z.toast: 700
```

### 0.5 Screen generation rule

```txt
Every screen below must be built from component instances. Do not recreate Button/Card/Input/Table manually.
Use exact coordinates for top-level sections; internal elements use component Auto Layout.
```

---

# 1. access-control.denied.no-treatment-relationship

```yaml
Frame: 1448x1086
Shell: Standard
Route: Patients / Access denied
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| Sidebar | 0 | 0 | 244 | 1086 | `Shell/Sidebar` active=Patients |
| Topbar | 244 | 0 | 1204 | 84 | `Shell/Topbar` |
| MainPanel | 258 | 104 | 780 | 908 | `Access/DeniedPanel` |
| RightRailTop | 1054 | 104 | 344 | 510 | `Card/NextActions` |
| RightRailBottom | 1054 | 638 | 344 | 374 | `Card/BlockedReason` |
| FooterDisclaimer | 244 | 1050 | 1204 | 24 | `Text/FooterDisclaimer` |

### MainPanel internal contract

```yaml
AccessDeniedPanel:
  padding: 36
  hero:
    x_rel: 220
    y_rel: 28
    w: 340
    h: 210
  title:
    y_rel: 260
    align: center
  body:
    y_rel: 316
    max_w: 440
    align: center
  divider:
    y_rel: 430
  requestDetailsTitle:
    y_rel: 462
  requestDetailsGrid:
    x_rel: 34
    y_rel: 500
    w: 712
    h: 220
    columns: 2
    rows: 2
  ctaRow:
    x_rel: 34
    y_rel: 744
    w: 712
    h: 56
    gap: 24
  immediateAccessCallout:
    x_rel: 34
    y_rel: 828
    w: 712
    h: 72
```

### Component tree

```txt
AccessDeniedPage
├─ Shell/Sidebar(active=Patients, recentType=Patients)
├─ Shell/Topbar
├─ Access/DeniedPanel
│  ├─ Illustration/ShieldLockOrbit
│  ├─ TextTitle "Access denied"
│  ├─ BodyCopy
│  ├─ RequestDetailsGrid
│  ├─ ButtonRow
│  └─ ImmediateAccessCallout
├─ NextActionsRail
└─ BlockedReasonRail
```

---

# 2. access-requests.create.clinical-justification-modal

```yaml
Frame: 1448x1086
Shell: Standard dimmed background
Overlay: ModalBackdrop opacity 52%
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| BackgroundAccessDenied | 0 | 0 | 1448 | 1086 | previous screen dimmed |
| ModalBackdrop | 0 | 0 | 1448 | 1086 | `Overlay/Backdrop` |
| AccessRequestModal | 290 | 226 | 860 | 730 | `Access/RequestModal` |

### Modal internal contract

```yaml
AccessRequestModal:
  padding: 24
  radius: 20
  Header: {x_rel: 24, y_rel: 24, w: 812, h: 54}
  PatientStrip: {x_rel: 24, y_rel: 88, w: 532, h: 70}
  ExplainerRail: {x_rel: 580, y_rel: 88, w: 256, h: 530}
  FormGrid:
    x_rel: 24
    y_rel: 178
    w: 532
    h: 150
    columns: 2
    gap: 20
  PurposeCards:
    x_rel: 24
    y_rel: 360
    w: 532
    h: 74
    columns: 3
    gap: 12
  Justification:
    x_rel: 24
    y_rel: 462
    w: 532
    h: 108
  Confirmation:
    x_rel: 24
    y_rel: 590
    w: 532
    h: 40
  FooterActions:
    x_rel: 484
    y_rel: 664
    w: 300
    h: 48
```

### Anchor/behavior

```yaml
BackdropClick: close modal
CloseButton: x_rel=816 y_rel=24
SubmitButton: disabled=false
FocusTrap: true
InitialFocus: Requested resource select
```

---

# 3. audit.logs.access-event-detail-panel

```yaml
Frame: 1448x1086
Shell: Standard
Route: Audit Logs / Drawer open
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| Sidebar | 0 | 0 | 244 | 1086 | active=Audit |
| Topbar | 244 | 0 | 1204 | 84 | standard |
| MainContent | 268 | 104 | 868 | 894 | Audit page content |
| DetailDrawer | 1148 | 84 | 300 | 1002 | `Audit/EventDrawer` |
| FooterDisclaimer | 244 | 1050 | 904 | 24 | footer |

### MainContent layout

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| PageHeader | 268 | 104 | 868 | 58 |
| MetricRow | 268 | 184 | 868 | 102 |
| FilterBar | 268 | 306 | 868 | 70 |
| EventsMetaRow | 268 | 390 | 868 | 30 |
| AuditTable | 268 | 432 | 868 | 496 |
| InfoCardsRow | 268 | 946 | 868 | 96 |

### Metric row

```yaml
columns: 4
gap: 16
card_w: 205
card_h: 102
```

### AuditTable columns

```yaml
row_h: 48
header_h: 40
columns:
  Timestamp: 140
  User: 120
  Role: 90
  Patient: 150
  Action: 130
  Resource: 140
  Result: 80
  TraceID: 110
```

### Drawer internal

```yaml
AuditEventDrawer:
  Header: {x_rel: 20, y_rel: 24, w: 260, h: 50}
  StatusEventRow: {x_rel: 20, y_rel: 82, w: 260, h: 32}
  Tabs: {x_rel: 20, y_rel: 138, w: 260, h: 44}
  MetadataSections:
    start_y_rel: 200
    section_gap: 20
```

---

# 4. auth.login.staff-sso-email-password

```yaml
Frame: 1448x1086
Shell: Auth split
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| LeftMarketingPane | 0 | 0 | 592 | 1086 | `Auth/MarketingPane` |
| RightAuthPane | 592 | 0 | 856 | 1086 | `Auth/LoginPane` |
| EnvironmentPill | 1190 | 30 | 170 | 44 | `EnvironmentPill` |
| LoginCard | 732 | 108 | 576 | 840 | `Auth/LoginCard` |
| FooterHelp | 760 | 1000 | 520 | 32 | auth footer |

### Left pane contract

```yaml
BrandLockup: {x: 62, y: 50, w: 310, h: 70}
Headline: {x: 62, y: 166, w: 440, h: 92}
Subtitle: {x: 62, y: 280, w: 430, h: 78}
FeatureList: {x: 62, y: 360, w: 430, h: 310}
Illustration: {x: 170, y: 650, w: 360, h: 260}
TrustFootnote: {x: 62, y: 1000, w: 430, h: 40}
```

### Login card internal

```yaml
LoginCard:
  padding: 40
  Title: y_rel=50
  SSOButton: y_rel=148 h=56
  Divider: y_rel=245
  EmailField: y_rel=320 h=52
  PasswordField: y_rel=434 h=52
  RememberForgotRow: y_rel=516 h=28
  EmailSubmit: y_rel=560 h=56
  SecurityBox: y_rel=668 h=124
```

---

# 5. auth.mfa.verify-identity-code

```yaml
Frame: 1448x1086
Shell: Auth centered
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| BackgroundWatermarkLeft | 0 | 420 | 250 | 360 | illustration watermark |
| BackgroundWatermarkRight | 1240 | 550 | 160 | 180 | lock watermark |
| BrandLockup | 540 | 50 | 370 | 70 | brand centered |
| MFACard | 382 | 154 | 684 | 690 | `Auth/MFACard` |
| TrustStrip | 230 | 872 | 988 | 112 | `Auth/TrustStrip` |
| FooterLinks | 500 | 1028 | 450 | 32 | footer |

### MFA card internal

```yaml
MFACard:
  padding: 48
  LockTile: {x_rel: 294, y_rel: 38, w: 64, h: 64}
  Title: {x_rel: 0, y_rel: 132, w: 588, h: 42, align: center}
  Notice: {x_rel: 96, y_rel: 220, w: 420, h: 52}
  OtpLabel: {x_rel: 96, y_rel: 306}
  OtpGroup: {x_rel: 96, y_rel: 336, w: 456, h: 60, gap: 18}
  CountdownRow: {x_rel: 96, y_rel: 424, w: 456, h: 28}
  DividerOr: {x_rel: 96, y_rel: 474, w: 456, h: 24}
  MethodSelect: {x_rel: 96, y_rel: 516, w: 456, h: 56}
  VerifyButton: {x_rel: 96, y_rel: 590, w: 456, h: 58}
```

---

# 6. dashboard.empty.workspace-onboarding-first-data

```yaml
Frame: 1672x941
Shell: Wide
Route: Dashboard / Empty
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| PageHeader | 318 | 112 | 930 | 56 |
| CustomizeButton | 1460 | 118 | 160 | 40 |
| EmptyHeroCard | 318 | 196 | 940 | 500 |
| RecentThreadsEmpty | 1276 | 196 | 330 | 350 |
| ActivityFeedEmpty | 1276 | 578 | 330 | 300 |
| SkeletonMetricRow | 318 | 716 | 940 | 170 |

### Internal grid

```yaml
SkeletonMetricRow:
  columns: 4
  gap: 16
  card_w: 220
  card_h: 170
```

---

# 7. dashboard.overview.action-success-toast

```yaml
Frame: 1672x941
Shell: Wide
Route: Dashboard / Populated / User menu open
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| PageHeader | 322 | 120 | 820 | 56 |
| MetricRow | 322 | 198 | 1058 | 134 |
| QuickTaskCard | 322 | 352 | 585 | 190 |
| RecentThreadsCard | 926 | 352 | 454 | 190 |
| RecentPatientsCard | 322 | 592 | 585 | 330 |
| DocumentStatusCard | 926 | 592 | 454 | 125 |
| SafetyAccessCard | 926 | 742 | 454 | 180 |
| UserDropdown | 1372 | 78 | 258 | 372 |

### User dropdown anchor

```yaml
anchor: UserMenuTrigger
alignment: top-right
offset_y: 8
z_index: dropdown
```

---

# 8. dashboard.overview.populated-hms-ai-workspace

```yaml
Frame: 1448x1086
Shell: Standard
Route: Dashboard / Populated with charts
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| PageHeader | 268 | 112 | 760 | 56 |
| CustomizeButton | 1240 | 118 | 160 | 40 |
| MetricRow | 268 | 184 | 1112 | 112 |
| QuickTaskCard | 268 | 318 | 600 | 170 |
| RecentThreadsCard | 888 | 318 | 492 | 170 |
| RecentPatientsCard | 268 | 512 | 600 | 326 |
| DocumentStatusCard | 888 | 512 | 492 | 122 |
| SafetyAccessCard | 888 | 658 | 492 | 180 |
| LookupChartCard | 268 | 860 | 560 | 150 |
| QueryVolumeCard | 848 | 860 | 532 | 150 |

### Metric row

```yaml
columns: 4
gap: 16
card_w: 266
card_h: 112
```

---

# 9. documents.dashboard.ocr-indexing-semantic-search

```yaml
Frame: 1448x1086
Shell: Standard
Route: Documents & OCR
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| PageHeader | 268 | 108 | 700 | 56 |
| UploadDropzone | 268 | 176 | 728 | 205 |
| FilterBar | 268 | 400 | 728 | 56 |
| DocumentsTable | 268 | 472 | 728 | 515 |
| SemanticSearchPanel | 1014 | 104 | 360 | 94 |
| MatchingChunksCard | 1014 | 218 | 360 | 420 |
| ProcessingPipelineCard | 1014 | 658 | 360 | 170 |
| StorageUsageCard | 1014 | 848 | 360 | 158 |

### Documents table columns

```yaml
DocumentName: 210
Patient: 150
Type: 100
Status: 90
OCRConfidence: 90
IndexedAt: 120
Actions: 40
row_h: 48
```

---

# 10. documents.ocr-review.needs-review-low-confidence

```yaml
Frame: 1448x1086
Shell: Standard
Route: Documents / OCR Review
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| BackLink | 258 | 100 | 160 | 24 |
| PageHeader | 258 | 128 | 420 | 56 |
| ActionButtons | 770 | 120 | 600 | 48 |
| AlertBanner | 258 | 190 | 1114 | 60 |
| DocumentHeader | 258 | 270 | 1114 | 70 |
| Tabs | 258 | 344 | 1114 | 44 |
| ThumbnailRail | 258 | 398 | 116 | 558 |
| ScannedPagePane | 390 | 398 | 382 | 558 |
| ExtractedTextPane | 788 | 398 | 304 | 558 |
| RightStack | 1110 | 398 | 262 | 558 |
| BottomInfo | 258 | 976 | 820 | 56 |

### RightStack internal

```yaml
cards:
  ProcessingTimeline: h=190
  FailureReasons: h=160
  ReviewChecklist: h=190
gap: 16
```

---

# 11. documents.upload.batch-ocr-progress-modal

```yaml
Frame: 1448x1086
Shell: Standard dimmed
Overlay: Modal
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| BackgroundDocumentsPage | 0 | 0 | 1448 | 1086 |
| ModalBackdrop | 0 | 0 | 1448 | 1086 |
| UploadModal | 282 | 174 | 884 | 720 |

### UploadModal internal

```yaml
Header: {x_rel: 24, y_rel: 24, w: 836, h: 54}
Dropzone: {x_rel: 24, y_rel: 90, w: 836, h: 146}
SelectedHeader: {x_rel: 24, y_rel: 252, w: 836, h: 28}
FileTable: {x_rel: 24, y_rel: 288, w: 836, h: 180}
Pipeline: {x_rel: 48, y_rel: 500, w: 780, h: 90}
ActionRow: {x_rel: 24, y_rel: 610, w: 836, h: 48}
SecureFooter: {x_rel: 24, y_rel: 664, w: 836, h: 48}
```

---

# 12. metrics.dashboard.impact-quality-summary

```yaml
Frame: 1448x1086
Shell: Standard
Route: Metrics & Impact
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| PageHeader | 268 | 110 | 640 | 60 |
| DateFilter | 1064 | 104 | 220 | 44 |
| FilterButton | 1300 | 104 | 90 | 44 |
| SyntheticNotice | 1120 | 162 | 270 | 32 |
| MetricRow | 268 | 204 | 1122 | 132 |
| LookupChart | 268 | 354 | 444 | 300 |
| QueryVolumeChart | 728 | 354 | 294 | 300 |
| QualitySafetyChart | 1038 | 354 | 352 | 300 |
| WorkflowImpactTable | 268 | 676 | 600 | 300 |
| UserFeedbackCard | 888 | 676 | 502 | 300 |

### Metric row

```yaml
columns: 4
gap: 16
card_w: 268
card_h: 132
```

---

# 13. patients.ai-summary.stream-citations-retrieving

```yaml
Frame: 1448x1086
Shell: Standard
Route: Chat / Patient summary / streaming
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| ChatPanel | 258 | 104 | 748 | 916 |
| EvidenceRail | 1024 | 104 | 374 | 916 |
| FooterDisclaimer | 244 | 1050 | 1204 | 24 |

### ChatPanel internal

```yaml
ContextHeader: {x_rel: 16, y_rel: 16, w: 420, h: 44}
ThreadHeader: {x_rel: 16, y_rel: 78, w: 500, h: 60}
UserBubble: {x_rel: 206, y_rel: 158, w: 486, h: 72}
AnswerCard: {x_rel: 60, y_rel: 250, w: 580, h: 470}
Composer: {x_rel: 16, y_rel: 760, w: 700, h: 130}
```

### EvidenceRail internal

```yaml
Header: h=60
Stepper: h=150
CitationCard1: h=210
CitationCardLoading2: h=150
CitationCardLoading3: h=150
FooterLink: y_rel=860
```

---

# 14. patients.empty.no-results-or-no-access

```yaml
Frame: 1672x941
Shell: Wide
Route: Patients / Empty
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| PageHeader | 296 | 114 | 720 | 56 |
| HeaderActions | 1120 | 112 | 270 | 44 |
| FilterBar | 296 | 204 | 1020 | 58 |
| EmptyHero | 296 | 262 | 1020 | 430 |
| EmptyTable | 296 | 692 | 1020 | 190 |
| SavedFiltersCard | 1332 | 204 | 300 | 250 |
| PatientAlertsCard | 1332 | 474 | 300 | 210 |
| QuickActionsCard | 1332 | 728 | 300 | 170 |

---

# 15. patients.list.scoped-alerts-recent-activity

```yaml
Frame: 1448x1086
Shell: Standard
Route: Patients / Scoped list
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| PageHeader | 268 | 108 | 650 | 56 |
| MetricRow | 268 | 178 | 824 | 108 |
| FilterSearch | 268 | 306 | 824 | 64 |
| FilterSelects | 268 | 382 | 824 | 54 |
| PatientsTable | 268 | 456 | 824 | 520 |
| SavedFiltersCard | 1112 | 104 | 286 | 270 |
| PatientAlertsCard | 1112 | 396 | 286 | 300 |
| RecentActivityCard | 1112 | 720 | 286 | 260 |

### Patients table columns

```yaml
Checkbox: 32
Patient: 170
MRN: 80
AgeSex: 90
Department: 120
Status: 90
Attending: 150
LastActivity: 110
Actions: 70
row_h: 52
```

---

# 16. patients.medication-review.cited-safety-answer

```yaml
Frame: 1448x1086
Shell: Standard
Route: Chat / Medication review / cited answer
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| ChatPanel | 258 | 104 | 748 | 916 |
| EvidenceRail | 1024 | 104 | 374 | 916 |
| FooterDisclaimer | 244 | 1050 | 1204 | 24 |

### ChatPanel internal

```yaml
ContextHeader: {x_rel: 16, y_rel: 16, w: 468, h: 44}
ThreadHeader: {x_rel: 16, y_rel: 78, w: 500, h: 60}
UserBubble: {x_rel: 230, y_rel: 170, w: 486, h: 72}
AnswerCard: {x_rel: 60, y_rel: 294, w: 580, h: 505}
Composer: {x_rel: 16, y_rel: 825, w: 700, h: 150}
```

### Evidence cards

```yaml
CitationCard1: {h: 230, title: Allergy Note}
CitationCard2: {h: 240, title: Medication List}
CitationCard3: {h: 240, title: Encounter Note}
gap: 16
```

---

# 17. chat.answer.safe-refusal-insufficient-evidence

```yaml
Frame: 1448x1086
Shell: Standard
Route: Chat / Safe refusal
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| ChatPanel | 258 | 104 | 748 | 916 |
| EvidenceRail | 1024 | 104 | 374 | 916 |

### ChatPanel internal

```yaml
ContextHeader: {x_rel: 16, y_rel: 16, w: 420, h: 44}
ThreadHeader: {x_rel: 16, y_rel: 78, w: 560, h: 60}
UserBubble: {x_rel: 250, y_rel: 170, w: 430, h: 90}
SafeRefusalCard: {x_rel: 78, y_rel: 278, w: 600, h: 430}
ActionCardsRow: {x_rel: 32, y_rel: 728, w: 670, h: 64}
Composer: {x_rel: 32, y_rel: 820, w: 670, h: 150}
```

### EvidenceRail internal

```yaml
NoEvidenceHero: {y_rel: 70, h: 240}
WhatThisMeansCard: {y_rel: 330, h: 120}
RetrievedButInsufficient: {y_rel: 500, h: 260}
CantFindHelp: {y_rel: 790, h: 90}
```

---

# 18. chat.landing.ai-hms-copilot

```yaml
Frame: 1672x941
Shell: Wide
Route: Chat / Landing
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| MainHeroPanel | 304 | 108 | 1340 | 790 |
| BotIllustration | 760 | 180 | 300 | 170 |
| HeroTitle | 690 | 360 | 420 | 44 |
| SuggestionCardsRow | 410 | 510 | 1060 | 140 |
| Composer | 500 | 690 | 880 | 150 |
| FooterDisclaimer | 288 | 910 | 1384 | 24 |

### Suggestion row

```yaml
columns: 4
card_w: 250
card_h: 136
gap: 20
```

---

# 19. chat.workspace.new-patient-context-thread

```yaml
Frame: 1448x1086
Shell: Standard
Route: Chat / New patient context thread
Figma Node ID: 28:479
```

### Top-level placement

| Layer | X | Y | W | H | Component |
|---|---:|---:|---:|---:|---|
| Sidebar | 0 | 0 | 244 | 1086 | `Shell/Sidebar` |
| Topbar | 244 | 0 | 1204 | 84 | `Shell/Topbar` |
| PageHeader | 268 | 108 | 640 | 43 | `Frame/PageHeader` |
| PatientSelector | 268 | 188 | 294 | 48 | `Frame/PatientSelector` |
| GeneralModeToggle | 790 | 188 | 234 | 48 | `Frame/GeneralModeToggle` |
| MainPromptPanel | 268 | 258 | 802 | 600 | `Frame/MainPromptPanel` |
| Composer | 268 | 875 | 802 | 136 | `Chat/Composer` |
| HelpRail | 1100 | 104 | 300 | 906 | `Frame/HelpRail` |
| FooterDisclaimer | 244 | 1050 | 359 | 15 | `Text/FooterDisclaimer` |

### MainPromptPanel internal

```yaml
WelcomeIllustration: {x_rel: 221, y_rel: 21, w: 360, h: 168}
TitleGroup:
  y_rel: 210
  title: "Your AI clinical assistant is ready to help"
  description: "Ask any question about this patient's care, records, and history."
TrustChipsRow:
  y_rel: 320
  chips:
    - { icon: "🔒", label: "Secure & permission-aware" }
    - { icon: "📄", label: "Citations you can trust" }
    - { icon: "⚙️", label: "Built for clinical workflows" }
PromptGrid:
  x_rel: 24
  y_rel: 388
  w: 754
  h: 184
  columns: 3
  rows: 2
  cards:
    - Card/Summarize: "Summarize this patient"
    - Card/Allergies: "Review allergies and medications"
    - Card/Labs: "Show latest labs"
    - Card/Discharge: "Draft discharge summary"
    - Card/Policies: "Search policies"
    - Card/FollowUp: "Find follow-up actions"
FooterText: "Try asking me about John Carter" (y_rel=360)
```

### HelpRail internal

```yaml
TopSection:
  x_rel: 16
  y_rel: 16
  w: 268
  h: 584
  Header: "✨ How this works"
  Items:
    - Item1: { icon: "security_shield_lock", title: "Ask anything clinical" }
    - Item2: { icon: "document_blue", title: "Get cited answers" }
    - Item3: { icon: "privacy_green_lock", title: "Permission-aware" }
    - Item4: { icon: "search_purple", title: "Built for your workflow" }
TipsContainer:
  x_rel: 0
  y_rel: 513
  w: 268
  h: 71
  title: "Tips for best results"
Card/NeedHelp:
  x_rel: 16
  y_rel: 805
  w: 268
  h: 85
  title: "Need help?"
  link: "View user guide ->"
```

### Composer internal

```yaml
InputRow:
  x_rel: 16
  y_rel: 16
  w: 770
  h: 40
  placeholder: "Ask a clinical question or request information..."
ActionRow:
  x_rel: 16
  y_rel: 68
  w: 770
  h: 40
  Buttons:
    - AskButton: "Ask"
    - SummaryButton: "Generate Summary"
    - StreamingToggle: "Streaming ON"
    - RefusalButton: "Safe Refusal Test"
```

### Component tree

```txt
SCR-011: New Patient Context Thread
├─ Shell/Topbar (active=SearchInput)
├─ Shell/Sidebar (active=Chat)
├─ PageHeader
├─ PatientSelector (John Carter MRN 104582, Status=Authorized)
├─ GeneralModeToggle (General knowledge mode, Status=Off)
├─ MainPromptPanel
│  ├─ WelcomeIllustration
│  ├─ TitleGroup
│  ├─ TrustChipsRow
│  │  ├─ Chip/Secure
│  │  ├─ Chip/Citations
│  │  └─ Chip/Workflows
│  └─ PromptGrid
│     ├─ Card/Summarize
│     ├─ Card/Allergies
│     ├─ Card/Labs
│     ├─ Card/Discharge
│     ├─ Card/Policies
│     └─ Card/FollowUp
├─ Chat/Composer
│  ├─ InputRow (Placeholder, SendIconButton)
│  └─ ActionRow (AskButton, SummaryButton, StreamingToggle, RefusalButton)
├─ HelpRail
│  ├─ TopSection (HeaderRow, ExplanationsContainer)
│  ├─ TipsContainer (Bullet list)
│  └─ Card/NeedHelp (Description, Link)
└─ Text/FooterDisclaimer
```

---

# 20. citations.viewer.verified-source-document

```yaml
Frame: 1448x1086
Shell: Standard dimmed
Route: Citation viewer modal
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| BackgroundChat | 0 | 0 | 1448 | 1086 |
| ModalBackdrop | 0 | 0 | 1448 | 1086 |
| DocumentViewerModal | 186 | 166 | 1076 | 764 |

### DocumentViewer internal

```yaml
Header: {x_rel: 0, y_rel: 0, w: 1076, h: 78}
ThumbnailRail: {x_rel: 0, y_rel: 78, w: 160, h: 632}
PdfToolbar: {x_rel: 160, y_rel: 78, w: 536, h: 62}
PdfCanvas: {x_rel: 180, y_rel: 140, w: 496, h: 548}
CitationPanel: {x_rel: 696, y_rel: 78, w: 380, h: 632}
TrustFooter: {x_rel: 0, y_rel: 710, w: 1076, h: 54}
```

### PDF canvas details

```yaml
PageFrame: {x_rel: 24, y_rel: 64, w: 452, h: 500}
Highlight:
  fill: Warning/100
  opacity: 80%
  radius: 2
```

---


# 21. patients.overview.ai-summary-hms-snapshot

```yaml
Frame: 1448x1086
Shell: Standard
Route: Patients / Patient Detail / Overview
State: Authorized patient, AI summary generated
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| BackLink | 268 | 104 | 140 | 24 |
| PatientHeaderCard | 256 | 126 | 744 | 196 |
| PatientTabs | 256 | 326 | 744 | 48 |
| AISummaryCard | 256 | 382 | 744 | 594 |
| GenerateSummaryButton | 256 | 990 | 190 | 44 |
| LastUpdatedText | 794 | 1002 | 184 | 24 |
| RightRail | 1020 | 100 | 344 | 900 |
| AllergyAlertsCard | 1020 | 100 | 344 | 128 |
| CurrentMedsCard | 1020 | 244 | 344 | 234 |
| LatestLabsCard | 1020 | 494 | 344 | 220 |
| EncountersCard | 1020 | 730 | 344 | 266 |

### PatientHeaderCard internal

```yaml
HeaderRow: {x_rel: 0, y_rel: 0, w: 744, h: 84, padding: 16, layout: horizontal}
Avatar: {x_rel: 18, y_rel: 24, w: 48, h: 48}
PatientNameBlock: {x_rel: 80, y_rel: 26, w: 350, h: 40}
AuthorizedChip: {x_rel: 568, y_rel: 26, w: 92, h: 28}
Actions: {x_rel: 674, y_rel: 24, w: 52, h: 32}
MetadataGridTop: {x_rel: 16, y_rel: 94, w: 710, h: 40, columns: 5}
MetadataGridBottom: {x_rel: 16, y_rel: 148, w: 710, h: 40, columns: 5}
```

### AISummaryCard internal

```yaml
Header: {x_rel: 0, y_rel: 0, w: 744, h: 64, padding: 18}
ConfidenceChip: {x_rel: 588, y_rel: 20, w: 112, h: 28}
ContentPanel: {x_rel: 16, y_rel: 68, w: 712, h: 480, padding: 16, layout: vertical, gap: 18}
ClinicalHistorySection: {h: 100}
CurrentMedsSection: {h: 86}
AllergiesSection: {h: 62}
RecentLabsStrip: {h: 72, columns: 6}
FollowUpNotesSection: {h: 92}
Footer: {x_rel: 0, y_rel: 550, w: 744, h: 44}
ViewSourcesButton: {x_rel: 584, y_rel: 558, w: 132, h: 36}
```

### RightRail internal

```yaml
RightRail:
  layout: vertical
  gap: 16
  width: 344
AllergyAlertsCard:
  tone: danger
  rows: 2
CurrentMedsCard:
  rows: 3
  show_more_link: true
LatestLabsCard:
  rows: 5
  status_chips: [High, Low, Normal, High, Low]
EncountersCard:
  timeline_rows: 3
  status_chips: [Active, Completed, Scheduled]
```

### Build rules

```txt
Use PatientDetailHeader and ClinicalRightRail instances. AISummaryCard content is Auto Layout vertical; do not manually position each paragraph after screen placement.
```

---

# 22. search.global.command-palette-recent-entities

```yaml
Frame: 1448x1086
Shell: Standard dimmed dashboard background
Route: Global Search / Command Palette
State: Open, empty query, recent entities visible
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| BackgroundDashboard | 0 | 0 | 1448 | 1086 |
| Backdrop | 0 | 0 | 1448 | 1086 |
| CommandPalette | 372 | 120 | 704 | 780 |
| SearchInput | 390 | 136 | 668 | 48 |
| RecentPatientsSection | 394 | 204 | 660 | 132 |
| RecentDocumentsSection | 394 | 362 | 660 | 132 |
| QuickCommandsSection | 394 | 520 | 660 | 194 |
| RecentThreadsSection | 394 | 734 | 660 | 118 |
| KeyboardHelpFooter | 372 | 860 | 704 | 40 |

### CommandPalette internal

```yaml
Panel:
  radius: 16
  fill: Colors/Bg/Surface
  shadow: Shadow/Modal
  padding: 16
  layout: vertical
  z_index: z.modal
SearchInput:
  h: 48
  radius: 12
  stroke: Colors/Primary/500
  focus_ring: true
SectionHeader:
  h: 28
  title_left: true
  view_all_right: true
EntityRow:
  h: 42
  avatar_or_icon: 32
  title_weight: 600
  meta_line: true
  action_keycap_right: true
QuickCommandRow:
  h: 44
  icon_tile: 32
  shortcut_keycap_right: true
Footer:
  h: 40
  fill: Colors/Bg/SurfaceTint
```

### Section content

```yaml
RecentPatients:
  - John Carter / MRN 104582 / 63 y/o / Male / Cardiology
  - Emily Davis / MRN 107331 / 54 y/o / Female / Endocrinology
  - Michael Lee / MRN 102773 / 72 y/o / Male / Cardiology
RecentDocuments:
  - Discharge_Summary_2025-05-10.pdf / John Carter / Discharge Summary
  - Lab Results_2025-05-09.pdf / John Carter / Lab Result
  - Cardiology Consult Note_2025-05-08.pdf / John Carter / Clinical Note
QuickCommands:
  - Start new clinical conversation
  - Generate patient summary
  - Upload document / shortcut: ⌘U
  - Open audit logs / shortcut: ⇧⌘A
  - View metrics / shortcut: ⇧⌘M
RecentThreads:
  - Discharge summary for John Carter
  - Lab result follow-up for Emily Davis
  - Anticoagulation guidance for Michael Lee
```

### Build rules

```txt
CommandPalette is a global overlay. It must not be nested inside Dashboard content. Use a single Backdrop layer and one CommandPalette frame. Rows use CommandEntityRow or CommandActionRow instances.
```

---

# 23. workspaces.environment-selector.synthetic-sandbox-training-production

```yaml
Frame: 1672x941
Shell: Wide dashboard
Route: Topbar / Environment selector
State: Synthetic Data dropdown open
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| DashboardContent | 288 | 84 | 1384 | 857 |
| EnvironmentTriggerActive | 1185 | 21 | 170 | 44 |
| EnvironmentPopover | 1124 | 70 | 372 | 330 |

### EnvironmentPopover internal

```yaml
Panel:
  radius: 14
  fill: Colors/Bg/Surface
  stroke: Colors/Border/Default
  shadow: Shadow/Dropdown
  padding: 18
  layout: vertical
  gap: 14
  z_index: z.dropdown
OptionRow:
  h: 50-58
  layout: horizontal
  icon_tile: 32
  text_block: fill
  status_chip: hug
Rows:
  SyntheticData: {icon: database, tone: success, chip: Current, chip_tone: success}
  Sandbox: {icon: flask, tone: warning, chip: Isolated, chip_tone: neutral}
  TrainingMode: {icon: graduation-cap, tone: purple, chip: Training, chip_tone: purple}
  ProductionData: {icon: lock, tone: danger, chip: Restricted, chip_tone: danger}
Divider: {h: 1, margin_top: 4, margin_bottom: 4}
InfoFooter: {h: 44, icon: info, text: current workspace notice}
```

### Anchor rules

```yaml
anchor_to: WideTopbar.EnvironmentPill
placement: bottom-start
offset_y: 8
right_edge_max: 1504
no_backdrop: true
close_on_outside_click: true
```

---

# 24. users.preferences.profile-security-system-status

```yaml
Frame: 1448x1086
Shell: Standard
Route: Settings / Profile
State: Profile tab active, system status visible
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 244 | 1086 |
| Topbar | 244 | 0 | 1204 | 84 |
| PageHeader | 268 | 108 | 680 | 56 |
| SettingsLocalNav | 268 | 184 | 176 | 390 |
| LocalNavDivider | 456 | 176 | 1 | 850 |
| MainSettingsColumn | 482 | 184 | 574 | 835 |
| ProfileCard | 482 | 218 | 574 | 86 |
| PreferencesCard | 482 | 340 | 574 | 344 |
| DisplayCard | 482 | 730 | 574 | 108 |
| SecurityCard | 482 | 884 | 574 | 128 |
| RightRail | 1088 | 176 | 300 | 860 |
| AccountSummaryCard | 1088 | 176 | 300 | 226 |
| SystemStatusCard | 1088 | 424 | 300 | 218 |
| UsageThisMonthCard | 1088 | 664 | 300 | 204 |
| NeedHelpCard | 1088 | 888 | 300 | 148 |

### SettingsLocalNav internal

```yaml
NavItem:
  h: 44
  radius: 10
  icon: 20
  padding_x: 14
Items:
  - Profile / active
  - Notifications
  - AI Preferences
  - Display
  - Security
  - Integrations
  - Data & Privacy
  - Billing
  - Advanced
```

### MainSettingsColumn internal

```yaml
ProfileCard:
  layout: horizontal
  avatar: 56
  verified_chip: true
  edit_button: right
PreferencesCard:
  row_h: 52
  rows:
    - Default startup page / select Dashboard
    - Show citations by default / toggle on
    - Enable streaming responses / toggle on
    - Default patient context / select Ask each time
    - Auto-save conversations / toggle on
    - Language / select English (US)
    - Date & time format / select May 10, 2025, 9:18 AM
    - Time zone / select GMT-07 Pacific
DisplayCard:
  groups:
    - Theme segmented: Light active, Dark, System
    - Density segmented: Comfortable active, Compact, Spacious
SecurityCard:
  rows:
    - Session timeout / select 30 minutes
    - Multi-factor authentication / Enabled
    - Active sessions / 3 active sessions
```

### RightRail internal

```yaml
AccountSummaryCard:
  status_chip: Active
  fields: [Role, Department, Account ID, Member since, Last sign in]
SystemStatusCard:
  status: All Systems Operational
  rows: [AI Assistant, Document Search, Data Indexing, Chat Service, Audit Logging, Notifications]
UsageThisMonthCard:
  progress_rows: [AI Queries, Document Indexing, Storage]
NeedHelpCard:
  links: [Help Center, Contact Support]
```

---

# 25. dashboard.overview.success-toast-stack

```yaml
Frame: 1672x941
Shell: Wide dashboard
Route: Dashboard / Populated
State: Success toast stack visible
```

### Top-level placement

| Layer | X | Y | W | H |
|---|---:|---:|---:|---:|
| Sidebar | 0 | 0 | 288 | 941 |
| Topbar | 288 | 0 | 1384 | 84 |
| DashboardContent | 288 | 84 | 1384 | 857 |
| ToastStack | 1352 | 842 | 292 | 132 |
| ToastRequestSubmitted | 1352 | 842 | 292 | 58 |
| ToastSettingsSaved | 1352 | 912 | 292 | 58 |

### ToastNotification internal

```yaml
Toast:
  w: 292
  h: 58
  radius: 12
  fill: Colors/Success/100
  stroke: Colors/Success/200
  shadow: Shadow/Card
  layout: horizontal
  padding_x: 16
  gap: 12
  z_index: z.toast
Icon:
  w: 28
  h: 28
  type: check-circle
  color: Colors/Success/600
Message:
  text_style: Typography/Body/Strong
  color: Colors/Text/Strong
CloseButton:
  w: 24
  h: 24
  align: right
Stack:
  layout: vertical
  gap: 12
  position: fixed bottom-right
  newest_on_top: true
```

### Build rules

```txt
ToastStack is a global overlay. Do not include it in DashboardContent Auto Layout. It should remain fixed when dashboard content scrolls.
```

---

## 26. Screen-level QA Checklist

For each screen:

- [ ] Frame size matches PNG.
- [ ] Sidebar/topbar dimensions match shell variant.
- [ ] Major sections placed with coordinates above.
- [ ] All content built using component instances.
- [ ] Overlay screen includes backdrop and correct z-index.
- [ ] Right rail width consistent.
- [ ] Tables use row component; no loose row shapes.
- [ ] Action buttons use Button component.
- [ ] Clinical answer includes disclaimer.
- [ ] Access/evidence states include audit/permission labels.
- [ ] Footer disclaimer visible unless auth screen.
