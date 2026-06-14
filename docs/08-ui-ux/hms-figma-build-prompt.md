# figma-build-prompt.md — Build Prompts & Execution Rules

> Mục tiêu: file này là prompt/brief để đưa cho Figma AI, plugin, hoặc designer khi build file. Nó ép quy trình theo thứ tự: **tokens → components → domain components → screens**, tránh lỗi “vẽ bằng lời” hoặc tạo documentation board thay vì UI thật.

---

## 0. One-line Objective

```txt
Create a reusable Figma design system and recreate the supplied AI-Powered Hospital Knowledge Assistant screens using component instances, exact layout contracts, Auto Layout, and tokenized styles.
```

---

## 1. Critical Instruction for Figma AI

Use this instruction at the top of every generation prompt:

```txt
Do not create a documentation board. Do not paste markdown text onto the canvas. 
Create actual Figma UI components: Frames, Auto Layout groups, Text layers, Vector/icon placeholders, component variants, and screen frames.
All final screens must use instances from the component library. 
Use the supplied layout coordinates for top-level frames.
```

---

## 2. Build Order

```txt
Step 1 — Create Figma pages
Step 2 — Create token styles and variables
Step 3 — Create base components
Step 4 — Create domain components
Step 5 — Create app shell templates
Step 6 — Create screen frames
Step 7 — Apply content overrides
Step 8 — QA against screenshots
Step 9 — Prepare prototype links
```

Do not skip component creation.

---

## 3. Prompt 1 — Create Tokens

```txt
Create a Figma page named "01 Tokens".
Create color variables using the token names from design-system.md:
- Color/Bg/App
- Color/Bg/Surface
- Color/Text/Strong
- Color/Primary/600
- Color/Success/600
- Color/Danger/600
- Color/Warning/500
- Color/Purple/600
- Color/Chart/Blue
- etc.

Create typography styles:
- Typography/Display
- Typography/H1
- Typography/H2
- Typography/H3
- Typography/Metric
- Typography/Body
- Typography/BodyStrong
- Typography/Caption
- Typography/CaptionStrong
- Typography/Button

Create effect styles:
- Effect/Shadow/Card
- Effect/Shadow/Modal
- Effect/Shadow/Popover
- Effect/FocusRing

Create spacing, radius, z-index notes as token cards only on the token page.
Token documentation cards are allowed only on the Tokens page, not in final UI screens.
```

Expected output:

```txt
01 Tokens
  Color styles
  Typography styles
  Effect styles
  Radius/spacing reference
```

---

## 4. Prompt 2 — Create Base Components

```txt
Create a Figma page named "03 Components / Base".
Create actual reusable components with variants, not descriptions.

Components to create:
1. Button
2. IconButton
3. Input/Text
4. Input/SearchCommand
5. Input/Select
6. Control/Checkbox
7. Control/RadioCard
8. Chip
9. Avatar
10. Card/Base
11. Divider
12. Progress/Bar
13. Progress/Stepper
14. Table/Container
15. Table/HeaderRow
16. Table/Row
17. Pagination

Each component must use:
- Auto Layout
- tokenized fills/strokes/text styles
- named child layers
- variants from figma-component-library.md
- focus/hover/disabled where applicable
```

Quality requirement:

```txt
A button must be a Frame with text/icon layers, not a rectangle with text detached.
A table row must be a component with cells, not a screenshot-like group.
```

---

## 5. Prompt 3 — Create Domain Components

```txt
Create a Figma page named "04 Components / Domain".
Create these domain components using base components as nested instances:

App shell:
- Shell/App/Standard
- Shell/App/Wide
- Shell/Sidebar
- Shell/Topbar
- Brand/Lockup
- Nav/SidebarItem
- Workspace/EnvironmentPill
- User/MenuTrigger
- User/Dropdown

Patient:
- Patient/ContextHeader
- Patient/SummaryStrip
- Patient/ListRow
- Patient/AlertCard
- Patient/MetricCard

Chat AI:
- Chat/UserBubble
- Chat/AnswerCard
- Chat/Composer
- Chat/SuggestionActionCard
- Chat/SafeRefusalCard
- Chat/StreamingAnswerCard

Evidence:
- Evidence/Rail
- Evidence/CitationCard
- Evidence/NumberBadge
- Evidence/SnippetBox
- Evidence/VerificationChecklist
- Evidence/NoEvidenceState

Documents & OCR:
- Documents/UploadDropzone
- Documents/UploadModal
- Documents/OCRReviewHeader
- Documents/PageThumbnailRail
- Documents/ScannedPagePane
- Documents/ExtractedTextPane
- Documents/ProcessingPipelineCard
- Documents/StorageUsageDonut

Audit & Access:
- Access/DeniedPanel
- Access/RequestDetailsGrid
- Access/RequestModal
- Audit/EventDrawer
- Audit/MetricCard
- Audit/EventsTable

Auth:
- Auth/MarketingPane
- Auth/LoginCard
- Auth/MFACard
- Auth/TrustStrip
```

Rules:

```txt
Use nested instances. Example: Access/RequestModal uses Input/Select, Control/RadioCard, Button, Card/Base.
Do not recreate base component shapes inside domain components.
```

---

## 6. Prompt 4 — Create App Shell Templates

```txt
Create page "05 Patterns".
Create these reusable templates:

1. Pattern/AppShell/Standard
Frame 1448x1086:
- Sidebar instance x=0 y=0 w=244 h=1086
- Topbar instance x=244 y=0 w=1204 h=84
- Content slot x=244 y=84 w=1204 h=1002

2. Pattern/AppShell/Wide
Frame 1672x941:
- Sidebar instance x=0 y=0 w=288 h=941
- Topbar instance x=288 y=0 w=1384 h=84
- Content slot x=288 y=84 w=1384 h=857

3. Pattern/Auth/Split
Frame 1448x1086:
- Left pane x=0 y=0 w=592 h=1086
- Right pane x=592 y=0 w=856 h=1086

4. Pattern/Overlay/Modal
- Backdrop full screen
- Centered modal slot
- z-index rules
```

---

## 7. Prompt 5 — Build Screens from Contracts

Use this prompt for each screen:

```txt
Create a Figma frame for [SCREEN_NAME] with size [W]x[H].
Use the shell/template specified in figma-screen-layout-contract.md.
Place top-level sections at the exact x/y/w/h coordinates from the contract.
Use component instances from the component library only.
Override text and icons to match the screenshot.
Use Auto Layout inside components.
Do not place Markdown description text on the UI frame.
Do not create a documentation board.
```

Example:

```txt
Create screen "access-control.denied.no-treatment-relationship".
Frame 1448x1086.
Use Shell/App/Standard.
Place:
- MainPanel x=258 y=104 w=780 h=908 using Access/DeniedPanel
- RightRailTop x=1054 y=104 w=344 h=510
- RightRailBottom x=1054 y=638 w=344 h=374
- FooterDisclaimer x=244 y=1050 w=1204 h=24
Match the screenshot content and state exactly.
```

---

## 8. Screen Build Batch Prompt

```txt
Build all 20 screens listed in figma-screen-layout-contract.md.
For each screen:
- use the exact frame size;
- use the exact shell variant;
- place all top-level objects with x/y/w/h from the contract;
- use instances from Components / Domain;
- apply content overrides;
- preserve active sidebar item;
- preserve right rails, modals, drawers, and overlay z-index;
- create a screenshot reference image next to each frame for manual QA if possible.
```

---

## 9. Component Instance Mapping

| Screen pattern | Main components |
|---|---|
| Access denied | `Access/DeniedPanel`, `Access/RequestDetailsGrid`, `Card/NextActions`, `Card/BlockedReason` |
| Access request modal | `Access/RequestModal`, `Patient/SummaryStrip`, `Input/Select`, `RadioCard`, `Textarea`, `Button` |
| Audit logs | `Audit/MetricCard`, `Audit/EventsTable`, `Audit/EventDrawer` |
| Auth login | `Auth/MarketingPane`, `Auth/LoginCard`, `Input/Text`, `Button` |
| MFA | `Auth/MFACard`, `OTPInput`, `Auth/TrustStrip` |
| Dashboard | `Card/Metric`, `Card/Section`, `Table/RecentPatients`, `DataViz` |
| Documents | `Documents/UploadDropzone`, `Documents/Table`, `SemanticSearchPanel`, `ProcessingPipelineCard` |
| OCR review | `OCRReviewHeader`, `PageThumbnailRail`, `ScannedPagePane`, `ExtractedTextPane`, `FailureReasonsCard` |
| Chat | `Patient/ContextHeader`, `Chat/UserBubble`, `Chat/AnswerCard`, `Chat/Composer`, `Evidence/Rail` |
| Citation viewer | `DocumentViewerModal`, `PdfThumbnailRail`, `CitationDetailsPanel` |
| Patients list | `MetricCard`, `PatientsDataTable`, `SavedFiltersCard`, `PatientAlertsCard` |
| Metrics | `MetricCard`, `LineChartCard`, `BarChartCard`, `WorkflowImpactTable`, `UserFeedbackCard` |

---

## 10. Rules to Prevent Layout Drift

```txt
1. Top-level containers must use fixed x/y/w/h from the screen contract.
2. Internal component content may use Auto Layout.
3. Do not use "space evenly" for dashboard cards unless specified.
4. Use exact sidebar width and topbar height.
5. Use fixed right rail width.
6. Use fixed modal size and center position.
7. Popovers/dropdowns must be anchored to their trigger.
8. Do not auto-center all content unless the screen contract says centered.
9. Tables must use row heights and column widths from the screen contract.
10. Citation rail cards must stack vertically with 16px gap.
```

---

## 11. How to Handle Images, Avatars, and Illustrations

```txt
Use AssetSlot components for illustrations and avatars.
If actual image assets are not provided, create clean placeholder shapes that match:
- bounding box,
- dominant color,
- soft 3D style,
- opacity,
- position.

Do not replace illustration slots with text descriptions.
```

Asset slots to create:

```txt
AssetSlot/LogoShieldCross
AssetSlot/Illustration/ShieldLockOrbit
AssetSlot/Illustration/AuthSecurity
AssetSlot/Illustration/MFAWatermarkShield
AssetSlot/Illustration/ChatBot
AssetSlot/Illustration/NoData
AssetSlot/Illustration/NoPatients
AssetSlot/DocumentThumbnail
AssetSlot/UserAvatar
AssetSlot/PatientAvatar
```

---

## 12. QA Prompt

After building screens, run this checklist:

```txt
Compare each generated frame with the source screenshot at 100% zoom.
Check:
- frame size;
- sidebar width;
- topbar height;
- content start x/y;
- right rail width;
- card row gaps;
- table row heights;
- modal dimensions;
- overlay opacity;
- active nav item;
- chips/status colors;
- typography hierarchy;
- footer disclaimer position;
- evidence/citation rail structure.
Report differences greater than 8px.
```

---

## 13. Expected Figma File Structure

```txt
00 Cover
01 Tokens
02 Foundations
03 Components / Base
04 Components / Domain
05 Patterns
06 Screens / App
  access-control.denied.no-treatment-relationship
  access-requests.create.clinical-justification-modal
  audit.logs.access-event-detail-panel
  dashboard.overview.populated-hms-ai-workspace
  documents.dashboard.ocr-indexing-semantic-search
  patients.medication-review.cited-safety-answer
  ...
07 Screens / Auth
  auth.login.staff-sso-email-password
  auth.mfa.verify-identity-code
08 QA Reference
99 Archive
```

---

## 14. Final Delivery Criteria

A correct Figma result:

- contains reusable components, not only screen drawings;
- screen components are instances;
- component variants are reusable across screens;
- screen layout matches supplied PNGs within small tolerance;
- colors/type/radius/shadow come from tokens;
- overlays/drawers/dropdowns use correct z-index;
- clinical safety and permission states are visible and consistent;
- no Markdown documentation appears inside final UI screens.
