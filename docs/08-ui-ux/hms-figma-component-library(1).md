# figma-component-library.md — Component Master Spec

> Mục tiêu: biến mô tả design system thành **component thật trong Figma**, không phải card text mô tả.  
> File này dùng để tạo các Component Master, Variants, Auto Layout, Constraints và Slots. Sau khi tạo xong component library, dựng screen bằng `figma-screen-layout-contract.md`.

---

## 0. Critical Build Rule

```txt
Do NOT create screens by manually drawing text descriptions.
Do NOT place Markdown paragraphs onto the canvas as UI.
Create reusable Figma components first.
Then create screen frames using component instances only.
```

A valid component in Figma must have:

```txt
FRAME node
Auto Layout direction
Width/height behavior
Padding
Gap
Fill
Stroke
Radius
Text layers
Icon slot layers
Variant properties
State properties
Constraints/resizing rules
```

---

## 1. Figma Library Page Structure

```txt
03 Components / Base
  01 Buttons
  02 Inputs
  03 Chips Badges
  04 Cards
  05 Tables
  06 Navigation
  07 Overlays

04 Components / Domain
  01 App Shell
  02 Patient
  03 Chat AI
  04 Evidence Citations
  05 Documents OCR
  06 Audit Access
  07 Auth
  08 Data Viz
  09 Empty Error States
```

---

## 2. Shared Component Properties

### 2.1 Auto Layout defaults

| Component type | Direction | Padding | Gap | Resize |
|---|---|---:|---:|---|
| Button | Horizontal | 12–16 x 10 | 8 | Hug x Fixed h |
| Input | Horizontal | 12 x 0 | 8 | Fill x Fixed h |
| Card | Vertical | 16–24 | 12–16 | Fill |
| Table row | Horizontal | 12–16 | 0 | Fill x Fixed h |
| Sidebar | Vertical | 16 | 8 | Fixed |
| Modal | Vertical | 24–32 | 20 | Fixed |
| Rail | Vertical | 16–20 | 16 | Fixed width |

### 2.2 Layer naming

```txt
ComponentName
  /bg
  /stroke
  /icon-left
  /content
    /title
    /subtitle
  /meta
  /actions
```

### 2.3 Common variant properties

```txt
size = sm | md | lg
state = default | hover | focus | selected | disabled | loading
tone = neutral | primary | success | danger | warning | purple | cyan
icon = none | left | right | both
```

---

# A. Base Components

---

## A1. Button

### Component: `Button`

```yaml
node: FRAME
auto_layout: horizontal
align: center
height:
  sm: 32
  md: 40
  lg: 48
padding:
  sm: 10 12
  md: 12 16
  lg: 14 20
gap: 8
radius: Radius/LG
```

### Variants

| property | values |
|---|---|
| `variant` | `primary`, `secondary`, `ghost`, `link`, `destructive`, `disabled` |
| `size` | `sm`, `md`, `lg` |
| `icon` | `none`, `left`, `right`, `both` |
| `loading` | `false`, `true` |

### Visual mapping

| Variant | Fill | Stroke | Text | Usage |
|---|---|---|---|---|
| Primary | `Primary/600` | none | white | Submit, Ask, Add Patient |
| Secondary | white | `Border/Default` | `Text/Strong` | Cancel, Generate Summary |
| Ghost | transparent | none | `Primary/600` | View all, Learn more |
| Link | transparent | none | `Primary/600` | Inline links |
| Destructive | white | `Danger/100` | `Danger/700` | Archive, Log out |
| Disabled | `Primary/100` or gray | none | `Text/Muted` | Inactive submit |

### Required children

```txt
Button
  IconLeft 16x16 optional
  Label Typography/Button
  IconRight 16x16 optional
```

---

## A2. Icon Button

### Component: `IconButton`

```yaml
node: FRAME
size:
  sm: 32x32
  md: 36x36
  lg: 40x40
auto_layout: center
radius: Radius/MD
fill: white or transparent
stroke: Border/Default optional
```

Variants:

```txt
tone = neutral | primary | danger | success
state = default | hover | focus | disabled
shape = rounded | circle
```

Usage: kebab menu, bookmark, close, export, eye, document action.

---

## A3. Text Input

### Component: `Input/Text`

```yaml
height: 44 or 48
radius: Radius/LG
fill: white
stroke: Border/Default
padding_left: 12
padding_right: 12
gap: 8
auto_layout: horizontal
```

Variants:

```txt
state = default | hover | focus | error | disabled
iconLeft = true | false
iconRight = none | keyboardHint | eye | chevron | send
```

Children:

```txt
IconLeft 20x20 optional
Placeholder/Value text
RightSlot optional
```

### Search input special

`Input/SearchCommand`

```yaml
height: 48
radius: 14
left_icon: search
right_slot: KeyboardHint ⌘K
```

---

## A4. Select Field

### Component: `Input/Select`

```yaml
height: 44 or 48
fill: white
stroke: Border/Default
radius: Radius/LG
direction: horizontal
padding: 12
gap: 8
```

Children:

```txt
IconLeft optional
TextStack
  Label optional
  Value
ChevronDown 16x16
```

Variants:

```txt
state = default | focus | error | disabled
density = compact | comfortable
```

---

## A5. Checkbox

### Component: `Control/Checkbox`

```yaml
size: 16x16 or 18x18
radius: 4
checked_fill: Primary/600
unchecked_fill: white
stroke: Border/Default
```

States: default, checked, focus, disabled.

---

## A6. Radio Card

### Component: `Control/RadioCard`

```yaml
node: FRAME
height: 68
radius: Radius/LG
fill: white
stroke: Border/Default or Primary/500 when selected
padding: 12
gap: 10
auto_layout: horizontal
```

Children:

```txt
RadioDot 18x18
IconTile optional
TextStack
  Title BodyStrong
  Subtitle Caption
```

Variants:

```txt
selected = true | false
tone = primary | success | warning | neutral
```

Usage: Access request purpose, clinical option card.

---

## A7. Chip / Badge

### Component: `Chip`

```yaml
height: 22 or 24
radius: Radius/Full or XS
padding_x: 8
gap: 4
auto_layout: horizontal
```

Variants:

| tone | bg | text | examples |
|---|---|---|---|
| success | Success/100 | Success/700 | Authorized, Verified, Allowed, Active |
| danger | Danger/100 | Danger/700 | Denied, OCR Failed, PHI - High |
| warning | Warning/100 | Warning/700 | OCR Processing, Needs Review |
| primary | Primary/100 | Primary/700 | Inpatient, Selected |
| purple | Purple/100 | Purple/600 | Clinical Note, AI Assistant |
| neutral | gray | Text/Muted | Archived |

Children: optional dot/icon, label.

---

## A8. Avatar

### Component: `Avatar`

```yaml
sizes: 24, 28, 32, 40, 48, 56
shape: circle
fill:
  initials: semantic pastel
  image: image fill
```

Variants:

```txt
type = initials | image
status = none | online | notification
```

Usage: doctor/user, patient, chat bubble.

---

## A9. Card Base

### Component: `Card/Base`

```yaml
node: FRAME
fill: Bg/Surface
stroke: Border/Default
radius: Radius/XL
padding: 16 or 20 or 24
gap: 12 or 16
auto_layout: vertical
shadow: none by default
```

Variants:

```txt
padding = compact | default | large
state = default | hover | selected | disabled
tone = neutral | success | danger | warning | primary | purple
```

---

## A10. Divider

### Component: `Divider`

```yaml
orientation: horizontal | vertical
stroke: Border/Subtle
thickness: 1
```

---

## A11. Progress Bar

### Component: `Progress/Bar`

```yaml
height: 6
radius: Full
track_fill: Border/Subtle
value_fill: tone
```

Variants: blue, green, orange, red, purple.

---

## A12. Stepper

### Component: `Progress/Stepper`

```yaml
direction: horizontal | vertical
dot_size: 20 or 24
line_thickness: 2
```

Variants:

```txt
state per step = complete | active | pending | failed
tone = primary | success | danger
```

Usage: OCR pipeline, access request explainer, evidence retrieval.

---

# B. Navigation Components

---

## B1. App Shell

### Component: `Shell/App/Standard`

```yaml
frame_size: 1448x1086
children:
  Sidebar: x=0 y=0 w=244 h=1086
  Topbar: x=244 y=0 w=1204 h=84
  ContentSlot: x=244 y=84 w=1204 h=1002
```

### Component: `Shell/App/Wide`

```yaml
frame_size: 1672x941
children:
  Sidebar: x=0 y=0 w=288 h=941
  Topbar: x=288 y=0 w=1384 h=84
  ContentSlot: x=288 y=84 w=1384 h=857
```

### Component: `Shell/App/Auth`

No sidebar. Used by login/MFA.

---

## B2. Sidebar

### Component: `Shell/Sidebar`

```yaml
width:
  standard: 244
  wide: 288
fill: Bg/Sidebar
stroke_right: Border/Subtle
padding: 16
auto_layout: vertical
gap: 16
```

Children:

```txt
BrandLockup
PrimaryNav
RecentSection
PermissionAwareCard
SidebarFooter
```

Constraints:

```txt
left: fixed
top: fixed
bottom: fixed
```

---

## B3. Brand Lockup

### Component: `Brand/Lockup`

```yaml
height: 58
direction: horizontal
gap: 12
padding: 0
```

Children:

```txt
LogoShieldCross 48x48
TextStack
  AI-Powered Hospital
  Knowledge Assistant
```

Auth variant: larger logo 60x60, text H2/H3.

---

## B4. Sidebar Nav Item

### Component: `Nav/SidebarItem`

```yaml
height: 44
radius: Radius/LG
padding_x: 12
gap: 12
auto_layout: horizontal
```

Variants:

```txt
active = true | false
```

Active:

```txt
fill: Primary/100
icon/text: Primary/600
```

Inactive:

```txt
fill: transparent
icon/text: Text/Default
```

---

## B5. Topbar

### Component: `Shell/Topbar`

```yaml
height: 84
fill: Bg/Surface
stroke_bottom: Border/Subtle
padding_left: 24
padding_right: 24
auto_layout: horizontal
align: center
gap: 16
```

Children:

```txt
GlobalSearch
Spacer
EnvironmentPill
SecurityShieldButton
UserMenuTrigger
```

Search placement:

```yaml
standard:
  x: 360
  y: 17
  w: 590
  h: 50
wide:
  x: 420
  y: 17
  w: 640
  h: 50
```

---

## B6. Environment Pill

### Component: `Workspace/EnvironmentPill`

```yaml
height: 44
radius: Radius/LG
fill: Success/50
stroke: Success/100
padding: 12 14
gap: 8
```

Children: database icon, label, chevron.

Variants: Synthetic, Sandbox, Training, Production.

---

## B7. User Menu Trigger

### Component: `User/MenuTrigger`

```yaml
height: 52
radius: Radius/LG
fill: white
stroke: Border/Default
padding: 8 12
gap: 8
```

Children: avatar 36, name/specialty text stack, chevron.

Selected/focus state: blue border/focus ring.

---

# C. Card Components

---

## C1. Metric Card

### Component: `Card/Metric`

```yaml
width: fill
min_height: 112
radius: Radius/XL
padding: 18 20
gap: 10
fill: white
stroke: Border/Default
auto_layout: vertical
```

Children:

```txt
HeaderRow
  Title CaptionStrong
  InfoIcon 14
MetricRow
  Value Typography/Metric
  TrendChip
FooterRow
  Baseline Caption
  SparklineSlot 72x28
```

Variants:

```txt
tone = blue | green | orange | purple | red
trend = up | down | neutral
```

---

## C2. Section Card

### Component: `Card/Section`

```yaml
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 20
gap: 16
auto_layout: vertical
```

Children: header row, body slot, footer slot.

---

## C3. Empty State Card

### Component: `Card/EmptyState`

```yaml
fill: white or SurfaceTint
stroke: Border/Default
radius: Radius/XL
padding: 32
align: center
gap: 16
```

Children:

```txt
IllustrationSlot
Title H2/H3
Description Body
ActionsRow
OptionalLink
```

Variants: dashboard, patients, recent threads, activity, no evidence.

---

## C4. Alert Banner

### Component: `Banner/Alert`

```yaml
height: 56 or content
radius: Radius/LG
padding: 14 16
gap: 12
auto_layout: horizontal
```

Variants:

```txt
tone = danger | warning | info | success
dismissible = true | false
```

Danger style for OCR low confidence.

---

# D. Table Components

---

## D1. Table Container

### Component: `Table/Container`

```yaml
fill: white
stroke: Border/Default
radius: Radius/XL
auto_layout: vertical
overflow: hidden
```

Children:

```txt
TableHeader
TableRows
Pagination
```

---

## D2. Table Header Row

```yaml
height: 44
fill: SurfaceTint or white
padding_x: 16
auto_layout: horizontal
```

Text: `Typography/CaptionStrong`, `Text/Default`.

---

## D3. Table Row

```yaml
height:
  compact: 48
  default: 56
  comfortable: 64
fill: white
stroke_bottom: Border/Subtle
padding_x: 16
auto_layout: horizontal
```

Variants:

```txt
state = default | hover | selected
```

Selected: `stroke: Primary/500`, light blue fill, full row border.

---

## D4. Pagination

```yaml
height: 52
direction: horizontal
align: center
padding: 12 16
gap: 8
```

Children: rows per page, range, page buttons, go-to-page input.

---

# E. Chat & AI Components

---

## E1. Patient Context Header

### Component: `Patient/ContextHeader`

```yaml
height: 44
radius: Radius/LG
fill: white
stroke: Border/Default
padding: 10 14
gap: 12
auto_layout: horizontal
```

Children:

```txt
PatientIcon/Avatar
Text: Patient: Name (MRN)
AuthorizedChip
InfoIcon optional
Actions optional
```

Variants: authorized, denied, general.

---

## E2. User Message Bubble

```yaml
max_width: 480
fill: Primary/50
stroke: Primary/200
radius: Radius/XL
padding: 18 20
gap: 8
align: right
```

Children: message text, timestamp/check row.

---

## E3. AI Answer Card

### Component: `Chat/AnswerCard`

```yaml
width: fill
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 20
gap: 16
auto_layout: vertical
```

Variants:

```txt
type = cited | streaming | safe-refusal
confidence = high | medium | low
```

Children:

```txt
HeaderRow
  AssistantIconTile
  Title optional
  StatusChip optional
ContentSlot
FooterRow
  FeedbackActions
  Disclaimer
  ConfidenceChip
```

---

## E4. Clinical Section

```yaml
direction: vertical
gap: 8
```

Children:

```txt
SectionTitle BodyStrong, color Cyan/600 or Text/Strong
BulletedList
InlineCitationLink
```

---

## E5. Chat Composer

### Component: `Chat/Composer`

```yaml
height: 120 to 150
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 16
auto_layout: vertical
gap: 12
```

Children:

```txt
InputRow
  PlaceholderText
  SendIconButton
ActionRow
  AskButton
  GenerateSummaryButton
  SafeRefusalTestButton
  Spacer
  StreamingToggle
```

Variants: idle, streaming, stopped.

---

## E6. Suggestion Action Card

```yaml
height: 96 or 110
fill: white
stroke: Border/Default
radius: Radius/LG
padding: 16
gap: 12
direction: horizontal
```

Children: icon tile, title/body, arrow.

---

# F. Evidence & Citation Components

---

## F1. Evidence Rail

### Component: `Evidence/Rail`

```yaml
width: 336 or 360
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 18
gap: 16
auto_layout: vertical
```

Children:

```txt
RailHeader
PermissionSubtitle
SourceCards
FooterLink
```

Variants:

```txt
state = populated | retrieving | no-evidence | insufficient
```

---

## F2. Citation Card

### Component: `Evidence/CitationCard`

```yaml
fill: white
stroke: Border/Default
radius: Radius/LG
padding: 14
gap: 12
auto_layout: vertical
```

Children:

```txt
Header
  NumberBadge 24
  SourceTitle
  TypeChip
  ThumbnailSlot optional
MetadataGrid
SnippetBox
RelevanceRow
```

Variants:

```txt
state = verified | loading | insufficient | external
density = default | compact
```

---

## F3. Number Badge

```yaml
size: 24x24
shape: circle
fill: Primary/600 or Primary/100 for loading
text: white or Primary/600
```

---

## F4. Snippet Box

```yaml
fill: SurfaceTint
stroke: Border/Default
radius: Radius/MD
padding: 12
```

Contains extracted source snippet. May have highlighted terms.

---

## F5. Verification Checklist

Rows:

```txt
Source Integrity  [Verified]
Permission Check  [Authorized]
Data Sensitivity  [PHI - High]
MFA               [Verified]
```

Use icon + label + chip.

---

# G. Documents & OCR Components

---

## G1. Upload Dropzone

```yaml
height: 150 or 170
fill: SurfaceTint
stroke: DashedUpload
radius: Radius/XL
padding: 24
align: center
gap: 16
```

Children: upload icon, title, support text, action buttons.

---

## G2. Document Row

Uses `Table/Row` with columns:

```txt
DocumentName
Patient
Type
StatusChip
OCRConfidence
IndexedAt
ActionsKebab
```

---

## G3. Processing Pipeline Card

```yaml
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 16
gap: 16
```

Children: horizontal stepper, summary stats grid.

---

## G4. Storage Usage Donut Card

```yaml
donut_slot: 110x110
legend_rows: 5
total_usage_footer
```

---

## G5. OCR Review Layout Components

### `Documents/OCRReviewHeader`

Contains document icon, filename, status chip, patient, upload date, type/source metadata.

### `Documents/PageThumbnailRail`

Fixed width 110–120, thumbnails with active border.

### `Documents/ScannedPagePane`

White page canvas with scanned document preview, highlights.

### `Documents/ExtractedTextPane`

Fixed width 300–340, search input, OCR text, low confidence highlights.

### `Documents/FailureReasonsCard`

Vertical list with warning icons.

---

# H. Audit & Access Components

---

## H1. Access Denied Panel

```yaml
fill: white
stroke: Border/Default
radius: Radius/XL
padding: 36
gap: 24
auto_layout: vertical
```

Children:

```txt
HeroIllustration ShieldLock
Title
Body
Divider
RequestDetailsGrid
CTA row
ImmediateAccessCallout
```

---

## H2. Request Details Grid

```yaml
grid: 2 columns x 2 rows
cell_height: 100
stroke: Border/Default
radius: Radius/XL
```

Cell children: icon tile, label, value, optional description.

---

## H3. Access Request Modal

```yaml
width: 860
height: auto around 730
radius: Radius/2XL
fill: white
shadow: Modal
padding: 24
direction: vertical
```

Body:

```txt
PatientSummaryStrip
FormGrid 2 columns
PurposeRadioCards 3 columns
Textarea
AuditConfirmation
FooterActions
RightExplainerRail
```

---

## H4. Audit Metric Card

Extends `Card/Metric` with icon tile top-right and tone.

---

## H5. Audit Event Drawer

```yaml
width: 300
height: full content
fill: white
stroke_left: Border/Default
padding: 20
gap: 16
```

Children: header, status, tabs, metadata sections, description.

---

# I. Auth Components

---

## I1. Auth Split Layout

```yaml
frame: 1448x1086
leftPane: x=0 y=0 w=580 h=1086
rightPane: x=580 y=0 w=868 h=1086
```

Left: logo, headline, feature list, illustration, trust footnote.  
Right: environment pill, login card, help footer.

---

## I2. Login Card

```yaml
width: 560
height: 760
fill: white
stroke: Border/Default
radius: Radius/2XL
shadow: Card
padding: 40
gap: 24
```

Children: title/subtitle, SSO button, divider, email/password form, remember/forgot, disabled submit, security assurance.

---

## I3. MFA Card

```yaml
width: 640
height: 580
fill: white
stroke: Border/Default
radius: Radius/2XL
shadow: Card
padding: 48
gap: 24
align: center
```

Children: lock tile, title/subtitle, email notice, OTP input group, countdown/resend, method selector, CTA.

---

## I4. OTP Input

```yaml
box_size: 60x60
radius: Radius/LG
stroke: Border/Default
focus_stroke: Primary/500
text: H2
```

Group: 6 boxes, gap 18.

---

# J. Data Visualization Components

---

## J1. Sparkline

```yaml
size: 72x28
stroke_width: 2
color: tone chart token
```

No axis, no grid.

---

## J2. Line Chart Card

```yaml
height: 180-240
chart_area: fill
legend: top
axis: left/bottom
```

Use chart grid and axis tokens.

---

## J3. Bar Chart Card

Same container; bars use `Chart/Blue` or `Chart/Purple`.

---

## J4. Donut Chart

```yaml
size: 110x110
hole: 58%
center_label: percentage
segments: chart colors
```

---

# K. Overlay Components

---

## K1. Modal Backdrop

```yaml
frame: full screen
fill: Bg/Overlay
opacity: 52%
z_index: overlay
```

---

## K2. Generic Modal

```yaml
fill: white
radius: Radius/2XL
shadow: Modal
z_index: modal
```

Children: header, body, footer.

---

## K3. User Dropdown

```yaml
width: 260
fill: white
stroke: Border/Default
radius: Radius/XL
shadow: Popover
padding: 12
gap: 8
```

Anchor: below `User/MenuTrigger`, right aligned.

---

## K4. Document Viewer Modal

```yaml
width: 1020
height: 760
fill: white
radius: Radius/2XL
shadow: Modal
```

Children:

```txt
Header h=78
Body horizontal
  ThumbnailRail w=150
  PDFPane flex
  CitationDetailsPanel w=300
Footer h=54
```

---


---

# M. Core UI Component Addendum — Video Checklist Coverage

> Phần này bổ sung các component phổ biến trong một Design System theo checklist: button, spacing, navigation, icon, radio/checkbox, toggle, tooltip, tabs, search, progress/step, loading, input, date picker, segmented control, card, list, empty state, popup, bottom sheet, inform/banner, toast/snackbar, badge/label/chip, collapse/expand.  
> Các component dưới đây phải được tạo thành **Component Master thật trong Figma**, không phải text mô tả trên canvas.

## M0. Coverage Matrix

| Component | Status in current UI | Figma master to create | Notes |
|---|---|---|---|
| Button | Used everywhere | `Button` | Already defined; add explicit primary/secondary/disabled/text rules. |
| Spacing | Tokenized | Tokens only | Already in design system; enforce 4px scale. |
| Navigation | Sidebar/topbar/tabs | `Shell/*`, `Nav/*`, `Tabs/*` | Add generic tabs master. |
| Icon | Used heavily | `Icon/Tile`, `Icon/Button`, icon styles | Add outline vs solid usage rules. |
| Radio | Access request purpose cards | `Control/Radio`, `Control/RadioCard` | Already partly defined; add simple radio. |
| Checkbox | Access confirmation, table selection | `Control/Checkbox` | Already defined. |
| Toggle | Streaming, settings, general knowledge | `Control/Toggle` | Add generic toggle. |
| Tooltip | Info icons on metrics/labels | `Overlay/Tooltip` | Missing; add. |
| Tabs | Patient profile, audit drawer, OCR review | `Tabs/Line`, `Tabs/Pill` | Missing as master; add. |
| Search bar | Topbar, filter rows, command palette | `Input/Search`, `CommandPalette/Search` | Search special exists; add usage details. |
| Progress & Step | Upload/OCR, evidence retrieval | `Progress/Bar`, `Progress/Stepper` | Already defined; add loading state relation. |
| Loading | AI streaming, evidence skeleton | `Feedback/Loading`, `Feedback/Skeleton` | Missing as master; add. |
| Input fields | Auth, forms, filters | `Input/Text` | Already defined. |
| Input spinner | Numeric count/page controls | `Input/Spinner` | Missing; add. |
| Date picker | Audit/metrics date range | `Input/DatePicker` | Missing; add. |
| Segmented | Theme/density, mode switching | `Control/Segmented` | Missing; add. |
| Carousel | Not visible in supplied screens | `Content/Carousel` | Add for future cards/document previews. |
| Banner | OCR alert, safety info | `Banner/Inform` | Alert banner exists; add semantic inform. |
| Card | Everywhere | `Card/Base`, domain cards | Already defined. |
| Item list | Sidebar recent items, menus, rails | `List/Item`, `List/Section` | Missing as generic master; add. |
| Empty state | Dashboard/patients/chat | `State/Empty` | Card/EmptyState exists; add generic state component. |
| Pop up | Modals/dropdowns/command palette | `Overlay/Dialog`, `Overlay/Popover` | Modal exists; add clearer popup taxonomy. |
| Bottom sheet | Not used desktop; useful mobile/responsive | `Overlay/BottomSheet` | Missing; add optional responsive master. |
| Inform | Safety, blocked, OCR warnings | `Feedback/Inform` | Missing as generic; add. |
| Snack message / Toast / Snackbar | Success stack | `Feedback/Toast`, `Feedback/Snackbar` | Missing; add. |
| Badge & Label | Status tags, counts, PHI | `Chip`, `Badge`, `Label` | Chip exists; add explicit label. |
| Chips | Filters, status, source type | `Chip` | Already defined. |
| Collapse & Expand | Rails, settings groups, source details | `Disclosure/Accordion` | Missing; add. |

---

## M1. Button Usage Contract

### Component: `Button`

Already defined in A1. Strengthen these product rules:

```yaml
ButtonVariants:
  type:
    - Primary
    - Secondary
    - Text
    - Ghost
    - Destructive
  state:
    - Default
    - Hover
    - Focus
    - Pressed
    - Disabled
    - Loading
  size:
    - SM
    - MD
    - LG
  icon:
    - None
    - Left
    - Right
    - Both
```

Rules:

- Use **one dominant Primary button per action area**. Example: `Submit request`, `Add Patient`, `Ask`, `Approve & Index`.
- Secondary buttons sit beside primary actions for non-destructive alternatives: `Cancel`, `Generate Summary`, `Request Access`.
- Text buttons are for low-emphasis actions: `View all`, `Learn more`, `Clear all`.
- Disabled buttons must still keep label visible and meet contrast for disabled text.
- Destructive actions must not use primary blue: `Archive`, `Log out`, delete/remove.

---

## M2. Icon Components and Icon State Rules

### Component: `Icon/Tile`

```yaml
Frame:
  size:
    - 32x32
    - 36x36
    - 40x40
    - 48x48
  radius: full or 12
  fill: semantic.100
Children:
  Icon: 16-24px
Variants:
  tone: blue | green | red | orange | purple | cyan | gray
  shape: circle | rounded-square
  emphasis: soft | solid
```

Icon rules:

- **Outline/line icons** are the default for nav, inactive state, table actions, toolbar icons.
- **Solid/filled icons** are reserved for active nav, selected state, critical status, success checks, and primary CTAs.
- Keep all icons visually simple: 1.5–2px stroke, rounded joins, no high-detail illustration inside 16–24px slots.
- Do not mix outline and filled versions randomly in one row. A row should have one visual grammar.

---

## M3. Generic Radio, Checkbox, Toggle

### Component: `Control/Radio`

```yaml
Frame:
  autoLayout: horizontal
  gap: 8
Children:
  RadioCircle: 18x18
  LabelGroup optional
Variants:
  state: default | hover | focus | selected | disabled | error
  label: true | false
```

Use when the user must choose **exactly one** option in a group. For rich options, use existing `Control/RadioCard`.

### Component: `Control/Toggle`

```yaml
Frame:
  w: 44
  h: 24
  radius: 999
  padding: 2
Children:
  Thumb: 20x20 radius full
Variants:
  state: off | on | disabled
  size: sm | md
```

Usage examples:

- `Streaming` toggle in chat composer.
- `General knowledge mode` toggle.
- Settings toggles: `Show citations by default`, `Enable streaming responses`, `Auto-save conversations`.

---

## M4. Tooltip

### Component: `Overlay/Tooltip`

```yaml
Frame:
  autoLayout: vertical
  width: hug, max 280
  padding: 8 10
  radius: 8
  fill: #081A48
  shadow: popover
Children:
  Text: Typography/Caption, color white
Variants:
  placement: top | right | bottom | left
  arrow: true | false
```

Rules:

- Tooltip explains an icon, metric, label, or healthcare-specific term in one short sentence.
- Never hide critical safety or clinical information only inside a tooltip.
- Info icons beside KPI titles, labels, and citations should use this component.

---

## M5. Tabs

### Component: `Tabs/Line`

```yaml
Frame:
  autoLayout: horizontal
  gap: 24
  height: 44
Children:
  TabItem:
    icon optional 18x18
    label
    activeUnderline: 2px
Variants:
  state: active | inactive | hover | disabled
  icon: true | false
```

Usage examples:

- Patient detail tabs: `Overview`, `Summary`, `Medications`, `Allergies`, `Labs`, `Documents`.
- OCR review tabs: `Review`, `Metadata`, `Activity`.
- Audit drawer tabs: `Overview`, `Raw Event`.

### Component: `Tabs/Pill`

Use for compact segmented navigation where the active tab is a filled/pale pill.

---

## M6. Search, Command Palette, and Filter Search

### Component: `Input/Search`

```yaml
Extends: Input/Text
Height: 44 or 48
Children:
  SearchIconLeft: 18-20px
  Placeholder
  KeyboardHint optional
  ClearButton optional
Variants:
  context: topbar | page-filter | command-palette | semantic-search
  state: default | focus | filled | disabled
```

Rules:

- Topbar search always includes keyboard hint `⌘K`.
- Command palette search uses focus ring immediately and appears inside overlay/popup.
- Semantic search combines search input + primary button in one row.

---

## M7. Loading, Skeleton, Progress, Step

### Component: `Feedback/LoadingSpinner`

```yaml
Frame:
  size: 16 | 20 | 24 | 32
Variants:
  tone: blue | green | neutral
  speed: normal | slow
```

### Component: `Feedback/Skeleton`

```yaml
Frame:
  radius: 6
  fill: #EEF3FB
Variants:
  type: line | block | avatar | card | chart
  width: fixed | fill
  animated: true | false
```

Usage examples:

- AI answer streaming placeholder lines.
- Evidence rail retrieving source cards.
- Empty dashboard placeholder metrics.

### Component: `Progress/Stepper`

Already defined in A12. Use for multi-stage flows:

- Uploading → OCR Parsing → Chunking → Embedding → Ready to index.
- Retrieving evidence → Validating citations → Streaming answer.
- Access request review lifecycle.

---

## M8. Input Spinner and Date Picker

### Component: `Input/Spinner`

```yaml
Frame:
  autoLayout: horizontal
  height: 40
  width: 112
  radius: 10
  stroke: border.default
Children:
  DecrementButton 32x32
  NumericValue text centered
  IncrementButton 32x32
Variants:
  state: default | focus | disabled | error
  size: sm | md
```

Use for numeric controls: rows per page, page number, quantity-like settings, timeout duration where appropriate.

### Component: `Input/DatePicker`

```yaml
Frame:
  autoLayout: horizontal
  height: 44
  minWidth: 180
  padding: 12
  radius: 10
Children:
  CalendarIcon 18x18
  DateText
  ChevronDown optional
Variants:
  mode: single | range | date-time
  state: default | focus | filled | disabled | error
```

Usage examples:

- Audit log `Date range` filter.
- Metrics dashboard range `Apr 13 – May 10, 2025`.
- Access request duration selector if expressed as exact dates.

---

## M9. Segmented Control

### Component: `Control/Segmented`

```yaml
Frame:
  autoLayout: horizontal
  gap: 4
  padding: 4
  radius: 12
  fill: surfaceTint
Children:
  SegmentItem x N
Variants:
  selection: single | multiple
  size: sm | md
```

### Component: `Control/SegmentItem`

```yaml
Frame:
  height: 36
  paddingX: 14
  radius: 8
Variants:
  state: active | inactive | hover | disabled
  icon: true | false
```

Usage examples:

- Settings theme: `Light`, `Dark`, `System`.
- Settings density: `Comfortable`, `Compact`, `Spacious`.
- Metrics chart granularity: `Daily`, `Weekly`, `Monthly`.

---

## M10. Card, Item List, Empty State

### Component: `List/Section`

```yaml
Frame:
  autoLayout: vertical
  gap: 4
Children:
  HeaderRow optional
  ListItem x N
Variants:
  density: compact | default | spacious
  divider: none | between | all
```

### Component: `List/Item`

```yaml
Frame:
  autoLayout: horizontal
  height: 44 | 52 | 64
  padding: 8 12
  gap: 12
Children:
  LeadingIconOrAvatar optional
  TextStack
  MetaOrAction optional
Variants:
  state: default | hover | selected | disabled
  leading: icon | avatar | status-dot | none
  trailing: chevron | shortcut | button | badge | none
```

Usage examples:

- Sidebar recent patients/threads/documents.
- User dropdown menu items.
- Command palette results.
- Alert/quick action lists in right rail.

### Component: `State/Empty`

```yaml
Frame:
  autoLayout: vertical
  align: center
  gap: 16
Children:
  Illustration optional
  Title
  Description
  ActionRow optional
Variants:
  context: page | card | table | rail
  action: none | one | two
```

---

## M11. Popup, Popover, Dialog, Bottom Sheet

### Component: `Overlay/Popover`

```yaml
Frame:
  width: 280-420
  radius: 14
  fill: surface
  shadow: popover
  stroke: border.default
Variants:
  anchor: top-left | top-right | bottom-left | bottom-right
  arrow: true | false
```

Usage examples:

- User account menu.
- Workspace/environment selector.
- Small command or filter menus.

### Component: `Overlay/Dialog`

Use existing `Modal` spec for blocking flows like access request and batch upload. Dialogs require a backdrop.

### Component: `Overlay/BottomSheet`

```yaml
Frame:
  width: fill
  minHeight: 320
  radiusTopLeft: 24
  radiusTopRight: 24
  fill: surface
  shadow: modal
Constraints:
  left: 0
  right: 0
  bottom: 0
Variants:
  height: compact | medium | full
  handle: true | false
```

Desktop screens do not currently use bottom sheets, but the component is required for responsive/mobile adaptations of patient actions, filters, source details, and upload options.

---

## M12. Inform, Banner, Toast, Snackbar

### Component: `Feedback/Inform`

```yaml
Frame:
  autoLayout: horizontal
  padding: 12 16
  gap: 12
  radius: 12
Children:
  StatusIcon
  TextStack
  Action optional
  Close optional
Variants:
  tone: info | success | warning | danger | neutral
  layout: inline | block
```

Usage examples:

- `AI can make mistakes` footer.
- OCR low confidence warning.
- Access policy/security notices.
- Synthetic/demo data notice.

### Component: `Feedback/Toast`

```yaml
Frame:
  autoLayout: horizontal
  width: 292-340
  minHeight: 56
  padding: 12 16
  gap: 12
  radius: 12
  fill: surface
  stroke: border.default
  shadow: popover
Constraints:
  right: 24
  bottom: 24
Children:
  StatusIcon
  Message
  CloseButton optional
Variants:
  tone: success | info | warning | danger
  action: none | text-button
```

### Component: `Feedback/Snackbar`

A snackbar is a wider bottom message bar. Use it when the message needs one short action button, e.g. `Undo`.

Rules:

- Toasts should auto-dismiss unless they report a critical error.
- Stack max: 3 visible toasts; newest appears at bottom-right or top of stack depending product decision.
- Do not use toast for critical clinical safety information.

---

## M13. Badge, Label, Chip

### Component: `Label`

```yaml
Text style: Typography/CaptionStrong
Color: text.strong or semantic.700
Variants:
  required: true | false
  helperIcon: true | false
```

### Component: `Badge/Count`

```yaml
Frame:
  minWidth: 18
  height: 18
  radius: 999
  paddingX: 6
Variants:
  tone: blue | green | red | orange | purple | gray
```

Use for counts like `Filters 2`, `Allergy Alerts 2`, saved filter counts, notification counts.

`Chip` remains the semantic status/tag component already defined in A7.

---

## M14. Carousel

### Component: `Content/Carousel`

```yaml
Frame:
  autoLayout: vertical
  gap: 12
Children:
  Viewport
  NavigationDots optional
  PrevNextControls optional
Variants:
  itemType: card | document-preview | image | chart
  controls: arrows | dots | both | none
  scrollSnap: true | false
```

Current desktop screens do not show a carousel. Include it as a future-safe content pattern for document previews, onboarding tips, education banners, and patient insight cards.

---

## M15. Collapse / Expand / Accordion

### Component: `Disclosure/Accordion`

```yaml
Frame:
  autoLayout: vertical
  radius: 12
Children:
  HeaderRow:
    LeadingIcon optional
    Title
    Meta optional
    Chevron
  ContentSlot
Variants:
  state: collapsed | expanded
  tone: neutral | info | warning | danger
  density: compact | default
```

Usage examples:

- Expand/collapse source metadata in evidence rail.
- Expand/collapse failure reasons in OCR review.
- Settings category groups on smaller screens.
- Audit raw event details.

---

## M16. Component Creation Priority

Create these components in this order:

```txt
1. Tokens and text styles
2. Button, Icon, Label, Chip, Badge
3. Input/Text, Input/Search, Select, DatePicker, Spinner
4. Checkbox, Radio, Toggle, Segmented
5. Tooltip, Inform, Toast/Snackbar, Loading/Skeleton
6. Card/Base, List/Item, EmptyState, Table
7. Tabs, Sidebar, Topbar, AppShell
8. Popover, Dialog/Modal, BottomSheet
9. Domain components: Evidence, Chat, Documents, Audit, Patient
10. Screen instances from layout contract
```


# L. Component QA Checklist

For each component:

- [ ] Uses tokenized color.
- [ ] Uses typography style.
- [ ] Has Auto Layout.
- [ ] Has named children/layers.
- [ ] Has required variants.
- [ ] Has focus/hover/disabled states.
- [ ] Has accessible label notes.
- [ ] Resizes according to constraints.
- [ ] Can be reused as instance in screens.
- [ ] Does not contain design documentation text unless it is part of UI.
