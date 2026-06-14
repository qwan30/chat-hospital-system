# design-system.md — AI-Powered Hospital Knowledge Assistant

> Mục tiêu: tài liệu này là **design language + token contract** cho sản phẩm. Nó không thay thế `figma-component-library.md` và `figma-screen-layout-contract.md`.  
> Khi build trong Figma: đọc file này trước để tạo styles/tokens, sau đó tạo component master từ `figma-component-library.md`, cuối cùng dựng màn hình bằng instance theo `figma-screen-layout-contract.md`.

---

## 0. Product DNA

### 0.1 Định vị sản phẩm

**AI-Powered Hospital Knowledge Assistant** là web app desktop dành cho bác sĩ/nhân viên bệnh viện để:

- tra cứu bệnh nhân, hồ sơ, tài liệu, guidelines;
- hỏi đáp lâm sàng bằng AI với citation;
- upload/OCR/index tài liệu;
- quản lý quyền truy cập patient record;
- audit toàn bộ sensitive access;
- đo lường impact và quality của AI assistant.

### 0.2 Tính cách giao diện

```txt
clinical, secure, calm, enterprise SaaS, evidence-first, permission-aware,
low-noise, high-trust, structured, auditable, assistant-with-guardrails
```

### 0.3 Nguyên tắc thiết kế

| Principle | Mô tả | UI biểu hiện |
|---|---|---|
| Permission-aware by default | Mọi dữ liệu bệnh nhân/tài liệu đi qua role, treatment relationship và audit. | Authorized chip, Access denied page, permission-aware sidebar card, audit-ready footer |
| Evidence-first answers | AI answer phải có citations, confidence và source rail. | Evidence & Citations rail, inline `[1]`, source card, verified source modal |
| Safe over complete | Thiếu bằng chứng thì refuse thay vì đoán. | Safe refusal card, low confidence chip, no supporting evidence state |
| Operational transparency | OCR/indexing/audit/status luôn có trạng thái rõ. | Processing pipeline, audit drawer, document timeline, progress bars |
| Next action clarity | Empty/error/blocked state luôn có bước tiếp theo. | CTA primary + secondary, help card, upload/request access links |
| Clinical readability | Text lâm sàng dễ scan, có heading, bullet, metadata. | H3 teal headings, compact body text, wide line-height, source metadata |
| Calm visual hierarchy | Nhiều trắng, border nhẹ, shadow thấp, màu trạng thái có ý nghĩa. | White cards, blue navigation, green success, red danger, orange warnings |

---

## 1. Design System Completeness Map

| # | Thành phần | Có trong system | Ghi chú |
|---:|---|---|---|
| 1 | Design Principles | Yes | Product DNA + safety principles |
| 2 | Design Tokens | Yes | Color, spacing, radius, shadow, border, opacity, z-index, motion |
| 3 | Typography System | Yes | Heading/body/caption/metric/token presets |
| 4 | Color System | Yes | Brand, surface, text, semantic, chart, clinical accents |
| 5 | Layout System | Yes | Desktop app shell, rails, modals, dashboards |
| 6 | Component Library | Yes | Chi tiết trong `figma-component-library.md` |
| 7 | Domain Components | Yes | Patient, evidence, OCR, audit, chat, auth |
| 8 | Patterns / Recipes | Yes | Chat, denied access, upload OCR, audit review |
| 9 | Content Guidelines | Yes | Clinical, refusal, CTA, labels, dates |
| 10 | Accessibility | Yes | Focus, contrast, keyboard, screen-reader labels |
| 11 | Motion & Data Visualization | Yes | Motion tokens, chart rules |
| 12 | Implementation & Governance | Yes | Build rules, naming, versioning, ownership |

---

## 2. Token Naming Convention

Use slash path naming for Figma Styles and Variables.

```txt
Color/Primary/600
Color/Text/Strong
Color/Border/Default
Typography/H1
Effect/Shadow/Card
Radius/LG
Spacing/6
Component/Button/Primary
Component/Card/Metric
Pattern/AppShell/Standard
```

For code export:

```txt
color.primary.600
color.text.strong
space.6
radius.lg
shadow.card
motion.duration.fast
```

---

## 3. Color System

### 3.1 Background, surface, border

| Token | Hex | Usage |
|---|---:|---|
| `Color/Bg/App` | `#F7FAFF` | App background, soft blue-white canvas |
| `Color/Bg/Page` | `#FFFFFF` | Main page content background |
| `Color/Bg/Surface` | `#FFFFFF` | Card, modal, drawer, table |
| `Color/Bg/SurfaceTint` | `#F9FBFF` | Tinted empty states, inner panels |
| `Color/Bg/Sidebar` | `#FAFCFF` | Sidebar background |
| `Color/Bg/Overlay` | `rgba(15, 23, 42, 0.52)` | Modal/dialog backdrop |
| `Color/Border/Subtle` | `#EEF3FB` | Divider, very light separators |
| `Color/Border/Default` | `#DCE6F7` | Cards, inputs, tables |
| `Color/Border/Strong` | `#BFD0EE` | Active hover/focus border |
| `Color/Border/Focus` | `#2F7AF7` | Selected card/row/input focus |

### 3.2 Typography colors

| Token | Hex | Usage |
|---|---:|---|
| `Color/Text/Strong` | `#081A48` | Page title, card title, metric |
| `Color/Text/Default` | `#24365F` | Main body |
| `Color/Text/Muted` | `#5B6B92` | Metadata, helper, timestamps |
| `Color/Text/Subtle` | `#8A98B8` | Placeholder, disabled |
| `Color/Text/Inverse` | `#FFFFFF` | Text on primary/dark buttons |
| `Color/Text/Link` | `#0B5CDF` | Links, inline citations, active labels |

### 3.3 Brand & interaction colors

| Token | Hex | Usage |
|---|---:|---|
| `Color/Primary/700` | `#004EC2` | Primary hover/pressed |
| `Color/Primary/600` | `#0B5CDF` | Primary CTA, active nav, links |
| `Color/Primary/500` | `#2F7AF7` | Icon accent, focus, chart line |
| `Color/Primary/300` | `#8BB8FF` | Illustration highlight |
| `Color/Primary/100` | `#EAF2FF` | Active nav bg, selected option, icon tile |
| `Color/Primary/50` | `#F5F9FF` | Light blue panels |

### 3.4 Semantic colors

| Token | Hex | Usage |
|---|---:|---|
| `Color/Success/700` | `#087443` | Success text |
| `Color/Success/600` | `#12A763` | Success icon, checkmark, positive chart |
| `Color/Success/100` | `#E8F8EF` | Authorized/verified/active chip bg |
| `Color/Success/50` | `#F2FBF6` | Success card tint |
| `Color/Danger/700` | `#B42318` | Denied/error text |
| `Color/Danger/600` | `#EF4444` | Error icon/destructive action |
| `Color/Danger/100` | `#FFF1F1` | Error alert/chip bg |
| `Color/Warning/700` | `#B54708` | Warning text |
| `Color/Warning/500` | `#F59E0B` | OCR processing, medium urgency |
| `Color/Warning/100` | `#FFF6E5` | Warning chip/bg |
| `Color/Purple/600` | `#7C3AED` | AI/refusal/citation accent |
| `Color/Purple/100` | `#F1E9FF` | AI/refusal tile/chip bg |
| `Color/Cyan/600` | `#0EA5B7` | Specialty/department accent |
| `Color/Cyan/100` | `#E6FAFC` | Cyan tile bg |

### 3.5 Chart colors

| Token | Hex | Usage |
|---|---:|---|
| `Color/Chart/Blue` | `#1265F0` | Primary metrics, bars, lookup line |
| `Color/Chart/Green` | `#18A957` | Positive trend / retrieval success |
| `Color/Chart/Orange` | `#FF6B00` | Denied/warning trend |
| `Color/Chart/Purple` | `#7C3AED` | Safe refusals / query volume secondary |
| `Color/Chart/Grid` | `#E7EDF8` | Chart grid lines |
| `Color/Chart/Axis` | `#6B7898` | Axis labels |

### 3.6 Color semantics

```txt
Blue   = navigation, primary action, links, selected/focus, AI interaction
Green  = allowed, authorized, verified, active, completed, access OK
Red    = denied, failed, blocked, destructive action, critical issue
Orange = warning, high risk, OCR processing, medium urgency
Purple = AI assistant, citations, safe refusal, patient query logged
Gray   = metadata, disabled, archived, skeleton, neutral background
```

---

## 4. Typography System

Recommended font: `Inter` or `SF Pro`. If unavailable, use `system-ui, -apple-system, BlinkMacSystemFont, Segoe UI`.

| Token | Size / Line | Weight | Usage |
|---|---:|---:|---|
| `Typography/Display` | 34 / 42 | 700 | Auth marketing headline, empty hero title |
| `Typography/H1` | 28 / 36 | 700 | Page title |
| `Typography/H2` | 22 / 30 | 700 | Modal title, large section |
| `Typography/H3` | 18 / 26 | 700 | Card title, chat thread title |
| `Typography/H4` | 16 / 24 | 700 | Section title inside card |
| `Typography/Metric` | 28 / 34 | 700 | KPI number |
| `Typography/Body` | 14 / 22 | 400 | Paragraphs, clinical answer |
| `Typography/BodyMedium` | 14 / 22 | 500 | Form values, row labels |
| `Typography/BodyStrong` | 14 / 22 | 600 | Label, table cell title |
| `Typography/Caption` | 12 / 16 | 400 | Metadata, helper |
| `Typography/CaptionStrong` | 12 / 16 | 600 | Badge text, table header |
| `Typography/Micro` | 11 / 14 | 500 | Small chips, page/chunk metadata |
| `Typography/Button` | 14 / 20 | 600 | Button labels |

Rules:

- Page titles use `Text/Strong`.
- Clinical answer body uses 14/22 or 15/23; do not compress line-height.
- Metadata uses `Text/Muted`.
- Metric values are large, bold, and never mixed with body style.
- Inline citations use link blue and square bracket style: `[1]`.

---

## 5. Spacing, Radius, Border, Shadow

### 5.1 Spacing scale

| Token | px | Usage |
|---|---:|---|
| `Spacing/1` | 4 | Micro gap, dot gap |
| `Spacing/2` | 8 | Icon-text gap, small chip padding |
| `Spacing/3` | 12 | Table cell compact padding |
| `Spacing/4` | 16 | Card internal gap, list row gap |
| `Spacing/5` | 20 | Card padding compact |
| `Spacing/6` | 24 | Standard page/card gap |
| `Spacing/8` | 32 | Modal padding, large section |
| `Spacing/10` | 40 | Hero spacing |
| `Spacing/12` | 48 | Auth layout spacing |
| `Spacing/16` | 64 | Large centered hero spacing |

### 5.2 Radius scale

| Token | px | Usage |
|---|---:|---|
| `Radius/XS` | 6 | Tiny chip, pill inside table |
| `Radius/SM` | 8 | Icon button, badge |
| `Radius/MD` | 10 | Sidebar nav, input internal button |
| `Radius/LG` | 12 | Inputs, buttons, cards small |
| `Radius/XL` | 16 | Major cards, dropdowns |
| `Radius/2XL` | 20 | Modals, auth cards |
| `Radius/3XL` | 24 | Large document viewer/modal |
| `Radius/Full` | 999 | Avatars, rounded pills |

### 5.3 Border tokens

| Token | Value | Usage |
|---|---|---|
| `Border/Hairline` | 1px `Border/Subtle` | Table dividers, panel separator |
| `Border/Default` | 1px `Border/Default` | Card/input/table |
| `Border/Selected` | 1.5px `Primary/500` | Selected row/card |
| `Border/Danger` | 1px `Danger/600` | OCR failed / danger alert |
| `Border/DashedUpload` | 1.5px dashed `Primary/300` | Upload/dropzone |

### 5.4 Shadows

| Token | CSS-ish value | Usage |
|---|---|---|
| `Effect/Shadow/Card` | `0 8px 24px rgba(20,38,80,.08)` | Dropdown, elevated card |
| `Effect/Shadow/Modal` | `0 18px 50px rgba(20,38,80,.18)` | Modal/dialog |
| `Effect/Shadow/Popover` | `0 12px 34px rgba(20,38,80,.16)` | Menu/popover/command palette |
| `Effect/FocusRing` | `0 0 0 3px rgba(11,92,223,.12)` | Focus state |

---

## 6. Layout System

### 6.1 Canvas sizes

| Mode | Frame | Usage |
|---|---:|---|
| Standard app | 1448 × 1086 | Most pages with sidebar/topbar |
| Wide app | 1672 × 941 | Dashboard/chat/patients wide variants |
| Modal over standard | 1448 × 1086 | Access request, upload OCR, citation viewer |
| Auth | 1448 × 1086 | Login, MFA |

### 6.2 App shell tokens

| Token | Standard | Wide |
|---|---:|---:|
| `Shell/Sidebar/Width` | 244 | 288 |
| `Shell/Topbar/Height` | 84 | 84 |
| `Shell/Content/PaddingX` | 24 | 28 |
| `Shell/Content/PaddingY` | 24 | 24 |
| `Shell/RightRail/Width` | 336–360 | 360–380 |
| `Shell/Grid/Gap` | 16 | 20 |

### 6.3 Core layout variants

#### App page with right rail

```ascii
+----------------------+------------------------------------------------+----------------+
| Sidebar              | Main content                                   | Right rail     |
| fixed                | fluid                                          | fixed          |
+----------------------+------------------------------------------------+----------------+
```

#### Dashboard grid

```ascii
Metric row: 4 equal cards
Body: left large column + right stack
Bottom: 2 chart cards or table + feedback cards
```

#### Chat + evidence rail

```ascii
Context header
Thread title
User bubble
AI card
Composer

Right: Evidence & Citations rail
```

#### Document dashboard

```ascii
Left: upload dropzone + filter table
Right: semantic search + pipeline + storage
```

#### Modal overlay

```ascii
Dimmed app shell
Centered modal frame
Header -> Body -> Footer
Optional side explainer rail
```

---

## 7. Iconography & Illustration

### 7.1 Icon style

- Stroke: 1.75–2 px.
- Corner: rounded.
- Size: 16, 18, 20, 24.
- Icon tiles: 36, 40, 44, 52.
- Tiles use pale semantic bg and matching icon color.

### 7.2 Icon groups

| Group | Icons |
|---|---|
| Security | shield, lock, verified shield, MFA, permission |
| Clinical | cross, document, lab flask, heart, lungs, stethoscope |
| AI/Search | bot, sparkle, magnifier, citation document |
| Admin/Ops | audit shield, charts, settings, upload cloud, database |
| Status | check, x, warning triangle, clock, bell, spinner |

### 7.3 Illustration style

- Soft 3D / glassmorphism.
- Primary blue + pale blue shadow.
- Low contrast; never compete with content.
- Used for empty states, auth, access denied, chat landing.
- In Figma component system, create as `AssetSlot/Illustration/*` with fixed bounding box. Use actual image asset when available; otherwise approximate with simple geometric placeholder.

---

## 8. Component Foundation Rules

Component building rules are expanded in `figma-component-library.md`.

Global rules:

1. Do not draw final screens directly with loose shapes.
2. Create component masters first.
3. Screens must use component instances.
4. Override content only; do not detach components unless creating a new variant.
5. All cards are Auto Layout vertical unless explicitly fixed.
6. Tables use row components; rows use cell components.
7. Evidence cards use fixed metadata structure.
8. Clinical content blocks must preserve spacing and citation formatting.
9. Overlay components need z-index and anchor rules.
10. Charts can use simplified vector placeholders, but must follow chart color tokens.

---


---

## 8A. Core Component Coverage Checklist

Phần này kiểm tra đầy đủ các component phổ biến trong Design System theo danh sách video và ánh xạ chúng vào sản phẩm HMS. Mục tiêu là để Figma/AI không chỉ biết “có component gì”, mà còn biết component đó thuộc nhóm nào, dùng khi nào và cần tạo master nào.

### 8A.1 Coverage summary

| Nhóm | Component | Trạng thái trong bộ file | Ghi chú bổ sung |
|---|---|---|---|
| Action | Button | Đã có, đã mở rộng | Primary, secondary, disabled, text/ghost, destructive, loading. |
| Foundation | Spacing | Đã có | Bắt buộc dùng scale bội số 4. |
| Navigation | Navigation | Đã có | Sidebar, topbar, tabs, pagination, command palette. |
| Visual | Icon | Đã có, đã mở rộng | Bổ sung rule outline/solid và icon tile. |
| Selection | Radio | Đã có | Simple radio + radio card. |
| Selection | Checkbox | Đã có | Checkbox thường + table checkbox + confirmation checkbox. |
| Selection | Toggle | Bổ sung | Streaming, settings, general knowledge mode. |
| Help | Tooltip | Bổ sung | Info icon, metric explanation, label help. |
| Navigation | Tabs | Bổ sung rõ hơn | Patient tabs, OCR review tabs, audit drawer tabs. |
| Search | Search bar | Đã có, đã mở rộng | Topbar, page filter, command palette, semantic search. |
| Progress | Progress & Step | Đã có | Upload/OCR pipeline, evidence retrieval, review flow. |
| Feedback | Loading | Bổ sung | Spinner, skeleton, streaming dots. |
| Input | Input fields | Đã có | Text, select, textarea, OTP. |
| Input | Input spinner | Bổ sung | Numeric control, rows/page, page number. |
| Input | Date picker | Bổ sung | Date range in audit/metrics. |
| Selection | Segmented | Bổ sung | Theme/density/chart granularity. |
| Display | Carousel | Bổ sung tùy chọn | Không có trong PNG hiện tại nhưng cần cho system đầy đủ. |
| Display | Banner | Đã có, mở rộng | Inform/alert/safety banner. |
| Display | Card | Đã có | Base card + domain cards. |
| Display | Item list | Bổ sung | Menu, recent items, command results, rail actions. |
| State | Empty state | Đã có | Page/card/table/rail variants. |
| Overlay | Pop up / Dialog | Đã có | Modal/dialog/popover taxonomy. |
| Overlay | Bottom sheet | Bổ sung tùy chọn | Responsive/mobile adaptation. |
| Feedback | Inform | Bổ sung | Info/success/warning/danger notice. |
| Feedback | Toast / Snackbar | Bổ sung | Success stack, undo/action snackbars. |
| Metadata | Badge & Label | Đã có, mở rộng | Count badge, field label, semantic chip. |
| Metadata | Chips | Đã có | Status/type/filter chips. |
| Disclosure | Collapse & Expand | Bổ sung | Accordion/disclosure for details. |

### 8A.2 Component taxonomy

```ascii
Design System Components
├─ Foundation
│  ├─ Color tokens
│  ├─ Typography tokens
│  ├─ Spacing / radius / border / shadow
│  └─ Icon style
├─ Actions
│  ├─ Button
│  ├─ IconButton
│  └─ TextButton
├─ Inputs
│  ├─ TextInput / Textarea
│  ├─ SearchInput
│  ├─ Select
│  ├─ DatePicker
│  ├─ InputSpinner
│  ├─ OTPInput
│  └─ Checkbox / Radio / Toggle / Segmented
├─ Navigation
│  ├─ Topbar
│  ├─ Sidebar
│  ├─ Tabs
│  ├─ Pagination
│  └─ CommandPalette
├─ Display
│  ├─ Card
│  ├─ Table
│  ├─ ListItem
│  ├─ EmptyState
│  ├─ Carousel
│  └─ Data visualization
├─ Feedback
│  ├─ Inform / Banner
│  ├─ Toast / Snackbar
│  ├─ Loading / Skeleton
│  ├─ ProgressBar
│  └─ Stepper
├─ Overlay
│  ├─ Tooltip
│  ├─ Popover
│  ├─ Dialog / Modal
│  └─ BottomSheet
└─ Disclosure
   └─ Collapse / Expand / Accordion
```

### 8A.3 Product-specific usage rules

- **Primary button**: chỉ 1 primary trong một vùng hành động chính. Ví dụ trong modal access request chỉ `Submit request` là primary, `Cancel` là secondary.
- **Spacing**: mọi khoảng cách dùng scale 4px: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64`. Không dùng số lẻ như 7, 13, 17.
- **Navigation**: authenticated screens luôn dùng sidebar + topbar. Auth screens không dùng sidebar.
- **Icon**: line icon cho inactive/default; solid hoặc filled tile cho active/selected/critical/success.
- **Radio vs checkbox**: radio cho chọn một, checkbox cho nhiều lựa chọn hoặc xác nhận điều khoản/audit.
- **Toggle**: dùng cho trạng thái bật/tắt tức thì; không dùng toggle cho hành động cần submit hoặc xác nhận pháp lý.
- **Tooltip**: chỉ giải thích phụ; không chứa thông tin clinical/safety bắt buộc.
- **Tabs**: dùng khi nội dung cùng cấp trong một entity, ví dụ patient detail hoặc OCR review.
- **Search bar**: topbar search là global; page search/filter là local; semantic search phải hiển thị nguồn/kết quả.
- **Progress/step/loading**: mọi tác vụ OCR, upload, evidence retrieval, AI streaming phải có trạng thái xử lý rõ ràng.
- **Input/date/spinner/segmented**: các input phải có label, state focus/error/disabled, helper khi cần.
- **Banner/inform/toast**: banner cho thông tin quan trọng trong flow; toast cho kết quả ngắn sau hành động; không dùng toast cho cảnh báo lâm sàng quan trọng.
- **Bottom sheet**: không dùng ở desktop hiện tại nhưng giữ component cho responsive/mobile.
- **Badge/chip/label**: chip mô tả trạng thái, badge đếm số, label định danh field/section.
- **Collapse/expand**: dùng cho metadata dài, audit raw data, source details, failure reasons.



## 9. Domain Patterns

### 9.1 Permission-aware retrieval pattern

Elements:

- patient/document context chip;
- authorized/denied/verified chip;
- audit access message;
- evidence rail or no evidence rail;
- footer disclaimer.

### 9.2 Safe refusal pattern

Use when evidence is missing/insufficient:

```txt
Icon: purple shield
Title: Insufficient evidence
Body: clear explanation
Next steps: search / upload / narrow question
Confidence: Low
Right rail: No supporting evidence + insufficient sources
```

### 9.3 Cited answer pattern

Use when answer is supported:

```txt
Clinical section headings
Bullets
Inline citations [1]
Confidence chip
Assistive output disclaimer
Evidence cards in right rail
```

### 9.4 OCR review pattern

Use when document confidence is low:

```txt
Red banner
Document header metadata
Review tabs
Original page viewer
Extracted text panel
Processing timeline
Failure reasons
Review checklist
```

### 9.5 Access request pattern

Use when access blocked:

```txt
Denied reason
Request access CTA
Modal form
Resource/duration/urgency/relationship
Purpose radio cards
Justification textarea
Audit confirmation
Submit with lock icon
```

---

## 10. Content Guidelines

### 10.1 Tone

- Professional, clinical, clear.
- No marketing fluff in clinical workflows.
- Explain access/safety constraints without blame.
- Always provide next action after blocked/refusal state.

### 10.2 Labels

| Pattern | Good |
|---|---|
| Access denied | “You do not currently have permission to view this patient record.” |
| Safe refusal | “I’m unable to answer that question based on the available, authorized evidence.” |
| Evidence | “Retrieved but insufficient” |
| OCR | “Low OCR confidence detected” |
| Audit | “All sensitive access attempts are logged and monitored.” |

### 10.3 Dates and metadata

- Date: `May 10, 2025`.
- Time: `9:18 AM`.
- Date range: `Apr 13 – May 10, 2025`.
- MRN format: `MRN 104582`.
- Page/chunk format: `Page: 1`, `Chunk: 2`.

### 10.4 Clinical safety footer

Use on AI outputs:

```txt
Assistive output — verify with clinical staff.
AI can make mistakes. Verify important information. Learn more
```

---

## 11. Accessibility

- All interactive controls need visible focus ring.
- Do not rely on color alone; combine status color with icon/text.
- Minimum text contrast: body 4.5:1, large text 3:1.
- All icon-only buttons require accessible labels.
- Keyboard order follows visual order.
- Modal traps focus and closes on Escape.
- Popover/menu anchors should be announced.
- Tables expose row/column headers.
- Charts provide numeric values and legends.
- Safe refusal and access denied should be accessible as status/alert regions.

---

## 12. Motion

| Token | Duration | Usage |
|---|---:|---|
| `Motion/Instant` | 80ms | Tiny hover |
| `Motion/Fast` | 120ms | Button/sidebar hover |
| `Motion/Base` | 180ms | Dropdown, tooltip |
| `Motion/Modal` | 220ms | Modal fade/scale |
| `Motion/Drawer` | 240ms | Right drawer slide |
| `Motion/AIStreaming` | 600–900ms loop | Dots/skeleton pulse |

Easing:

```txt
ease-out: cubic-bezier(.16, 1, .3, 1)
ease-in-out: cubic-bezier(.4, 0, .2, 1)
```

---

## 13. Data Visualization Rules

- Chart cards use white surface + subtle border.
- Axis labels are muted and small.
- Grid lines are subtle.
- Use semantic chart color consistently.
- Do not overdecorate.
- KPI cards always show:
  - title,
  - value,
  - comparison chip,
  - baseline text,
  - small sparkline or icon.

Chart types:

| Use case | Chart |
|---|---|
| Lookup time trend | Line chart |
| Query volume | Bar chart |
| Retrieval success / safe refusal | Area + line |
| Storage usage | Donut |
| Workflow improvement | Table + progress bar |
| Mini metrics | Sparkline |

---

## 14. Implementation & Governance

### 14.1 Figma pages

```txt
00 Cover
01 Tokens
02 Foundations
03 Components / Base
04 Components / Domain
05 Patterns
06 Screens / App
07 Screens / Auth
08 Prototypes
99 Archive
```

### 14.2 Naming convention

```txt
Button/Primary/MD
Button/Secondary/MD
Card/Metric
Card/PatientSummary
Shell/Sidebar/Standard
Shell/Topbar/Standard
Chat/AnswerCard/Cited
Evidence/CitationCard/Verified
Documents/OCRReviewPanel/LowConfidence
```

### 14.3 Versioning

Use semantic version:

```txt
v0.1 Initial extraction from PNG
v0.2 Figma component contracts
v0.3 Screen geometry contracts
v1.0 Ready for implementation
```

### 14.4 Ownership

| Area | Owner |
|---|---|
| Tokens | Design systems |
| Clinical copy | Clinical safety / product |
| Evidence & refusal patterns | AI safety + product |
| OCR/document workflows | Platform/document team |
| Audit/access | Security/compliance |
| Components | Design systems + frontend |

---

## 15. Build Checklist

Before generating screens:

- [ ] Create color variables.
- [ ] Create typography styles.
- [ ] Create effects/radius tokens.
- [ ] Create base components.
- [ ] Create domain components.
- [ ] Validate component variants.
- [ ] Build app shell.
- [ ] Build screens only with component instances.
- [ ] Check screenshot match at 100% zoom.
- [ ] Check focus/keyboard/modal behavior.
- [ ] Check clinical safety disclaimers.
