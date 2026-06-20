# HMS AI Copilot — Frontend UI Fix Design System

> Project: **AI-Powered Hospital Knowledge Assistant**  
> Purpose: one practical design-system contract for fixing the current React/shadcnUI frontend based on the latest screenshots and existing project docs.  
> Version: **2.1 — UI Fix Contract**  
> Scope: login, app shell, sidebar/topbar, user dropdown, patients, chat, documents, dashboard error/empty states.  
> Primary implementation stack: **React / TanStack Start, shadcnUI, Radix UI, Tailwind CSS, Lucide React**.

---

## 0. How to use this file

Use this file as the frontend repair contract.

Implementation order:

```txt
1. Fix global tokens in globals.css / Tailwind theme.
2. Fix AppShell: Sidebar, Topbar, BrandLockup, content grid, footer.
3. Fix overlay primitives: DropdownMenu, Popover, Dialog, Tooltip, z-index.
4. Fix auth/login layout and background layering.
5. Fix page templates: patients, chat, documents, dashboard.
6. Run visual QA against screenshots.
```

Do not patch each page randomly. Most current UI problems come from broken shared primitives:
`BrandLockup`, `AppShell`, `Topbar`, `DropdownMenu`, `Card`, `Input`, `Table`, and page grid templates.

---

## 1. Current screenshot audit

### 1.1 High-priority visual issues

| Area | Problem visible in screenshots | Likely root cause | Required fix |
|---|---|---|---|
| Logo / brand | Logo is tiny, cropped, blurry, or almost invisible in sidebar/topbar/login. Some screens show a small broken-looking rectangle instead of a clean icon. | Using raster screenshot/asset without fixed container, wrong `object-fit`, missing fallback, inconsistent brand component. | Build one `BrandLockup` component. Use one SVG or clean PNG asset inside a fixed 40–48px logo tile. Apply `object-contain`, no stretching. Never paste logo as background image. |
| App shell | Sidebar width and topbar alignment are inconsistent between pages. Documents page has overly dark vertical divider. | Hardcoded per-page layout instead of one shell contract. Borders using text/strong color instead of border token. | Use one `AppShell` with fixed desktop variables: sidebar `256px` in code, topbar `84px`, content padding `24px`. Border must be `--color-border-subtle`, not navy/black. |
| Login background | Doctor/hospital image sits behind the login card and competes with form content. The form visually “floats on top of faces”. | Background image layer is not masked/scrimmed; right pane mixes decorative image and form area. | Split auth layout: left marketing pane + right form pane. If using hospital image, place it as a decorative layer with `opacity: 0.18–0.28`, `blur: 0–2px`, and a white/blue gradient scrim. Login card must sit on clean surface. |
| User dropdown | Dropdown overlaps unrelated page controls, looks blurry/low-focus, and does not feel anchored to the avatar trigger. | Dropdown rendered inside page flow or wrong absolute positioning/z-index. Possible missing Radix portal. | Use shadcn/Radix `DropdownMenuContent` with `align="end"`, `sideOffset={8}`, `Portal`, `z-index: dropdown`, opaque white surface, `shadow-popover`, no backdrop blur. |
| Patients page | Right rail, filters, patient list, and dropdown feel crowded. Some controls look like they belong to the dropdown. | Page grid lacks clear main/rail columns; dropdown and page controls share same visual plane. | Use `PageGrid` = `main minmax(0,1fr)` + `rail 360–392px`, gap `24px`. Keep filter controls in main toolbar only. |
| Chat page | Suggestion chip floats awkwardly; safe-refusal card is not aligned to a clear message column; composer is too detached from conversation. | Chat layout not based on a fixed thread column + right rail + sticky composer. | Use `ChatLayout`: thread column `minmax(680px, 1fr)`, right rail `420px`, composer sticky bottom inside thread column. |
| Documents page | Sidebar/topbar borders are too dark; upload area/table/right rail are not using consistent grid; table appears clipped. | Border token mismatch and page height/scroll handling not centralized. | Documents page must use `DocumentsGrid`: main `minmax(0,1fr)`, rail `360px`, vertical scroll in content, table container max-height with sticky header. |
| Dashboard | Error state is just red text inside a huge empty canvas. | No domain error state component. | Replace with `DashboardErrorState` card: icon, title, explanation, retry CTA, secondary “view system status”, and optional skeleton fallback. |
| Cards / borders | Many cards have heavy navy border. Clinical UI should be calm; borders should support hierarchy, not dominate. | `border` color hardcoded to `#081A48` or similar strong text color. | Default card border must be `--color-border-default`; page dividers use `--color-border-subtle`; focus only uses `--color-border-focus`. |
| Inputs | Inputs have strong outline even when not focused. | Focus style applied as default style. | Default input = subtle border. Focus = `border-focus + focus-ring`. Hover = `border-strong`. |
| Third-party overlays | Bottom-left circular dev overlay and right blue sparkle widget appear in screenshots. | Browser extension/dev widget, not product UI. | Ignore for product design. If it is part of app, move into controlled `AssistantFloatingButton` with clear spec and z-index below dropdown/modal. |

---

## 2. Design principles for this project

```txt
clinical, secure, calm, enterprise SaaS, evidence-first, permission-aware,
low-noise, high-trust, structured, auditable, readable, deterministic
```

### Non-negotiable UI rules

1. **Component-first**: pages must be composed from `components/ui` primitives and domain components. Do not create one-off page-only shapes for common UI.
2. **No hardcoded colors**: use CSS variables and Tailwind token aliases.
3. **No hardcoded layout magic per page**: shell, topbar, sidebar, card, rail, dropdown are shared.
4. **Safe clinical states must be explicit**: error, empty, no evidence, access denied, loading, and fetch failure need designed states.
5. **Overlays always use Portal**: dropdown, dialog, sheet, tooltip, popover, command palette.
6. **Focus is visible and deterministic**: keyboard users must see `focus-ring`.
7. **Decorative images never reduce readability**: use masking/scrim/opacity; never place busy image directly under form text.

---

## 3. Foundation tokens

### 3.1 Color tokens

Use these as CSS variables in `globals.css`.

```css
:root {
  /* Brand / Primary */
  --color-primary-50: #F5F9FF;
  --color-primary-100: #EAF2FF;
  --color-primary-300: #8BB8FF;
  --color-primary-500: #2F7AF7;
  --color-primary-600: #0B5CDF;
  --color-primary-700: #004EC2;

  /* App backgrounds */
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

  /* Text */
  --color-text-strong: #081A48;
  --color-text-default: #24365F;
  --color-text-muted: #5B6B92;
  --color-text-subtle: #8A98B8;
  --color-text-inverse: #FFFFFF;
  --color-text-link: #0B5CDF;

  /* Semantic */
  --color-success-50: #F2FBF6;
  --color-success-100: #E8F8EF;
  --color-success-600: #12A763;
  --color-success-700: #087443;

  --color-danger-50: #FFF7F7;
  --color-danger-100: #FFF1F1;
  --color-danger-600: #EF4444;
  --color-danger-700: #B42318;

  --color-warning-50: #FFFBEB;
  --color-warning-100: #FFF6E5;
  --color-warning-500: #F59E0B;
  --color-warning-700: #B54708;

  --color-purple-100: #F1E9FF;
  --color-purple-600: #7C3AED;

  --color-cyan-100: #E6FAFC;
  --color-cyan-600: #0EA5B7;

  /* Charts */
  --color-chart-blue: #1265F0;
  --color-chart-green: #18A957;
  --color-chart-orange: #FF6B00;
  --color-chart-purple: #7C3AED;
  --color-chart-grid: #E7EDF8;
  --color-chart-axis: #6B7898;

  /* Effects */
  --shadow-card: 0 8px 24px rgba(20, 38, 80, 0.08);
  --shadow-modal: 0 18px 50px rgba(20, 38, 80, 0.18);
  --shadow-popover: 0 12px 34px rgba(20, 38, 80, 0.16);
  --effect-focus-ring: 0 0 0 3px rgba(11, 92, 223, 0.12);

  /* Radius */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 20px;
  --radius-3xl: 24px;
  --radius-full: 9999px;

  /* Shell */
  --shell-sidebar-w: 256px;
  --shell-topbar-h: 84px;
  --shell-content-px: 24px;
  --shell-content-py: 24px;

  /* z-index */
  --z-base: 0;
  --z-sidebar: 10;
  --z-topbar: 20;
  --z-rail: 30;
  --z-dropdown: 200;
  --z-drawer: 250;
  --z-backdrop: 500;
  --z-modal: 600;
  --z-toast: 700;
}
```

### 3.2 Tailwind semantic mapping

Recommended class aliases:

```txt
bg-app             = background: var(--color-bg-app)
bg-surface         = background: var(--color-bg-surface)
bg-surface-tint    = background: var(--color-bg-surface-tint)
bg-sidebar         = background: var(--color-bg-sidebar)

text-strong        = color: var(--color-text-strong)
text-default       = color: var(--color-text-default)
text-muted         = color: var(--color-text-muted)
text-subtle        = color: var(--color-text-subtle)

border-subtle      = border-color: var(--color-border-subtle)
border-default     = border-color: var(--color-border-default)
border-strong      = border-color: var(--color-border-strong)
border-focus       = border-color: var(--color-border-focus)

shadow-card        = box-shadow: var(--shadow-card)
shadow-popover     = box-shadow: var(--shadow-popover)
shadow-modal       = box-shadow: var(--shadow-modal)
```

### 3.3 Typography scale

| Token | CSS / Tailwind class | Weight | Usage |
|---|---|---:|---|
| Display | `text-[34px] leading-[42px]` | 700 | Auth hero, major empty state |
| H1 | `text-[28px] leading-[36px]` | 700 | Page title |
| H2 | `text-[22px] leading-[30px]` | 700 | Modal title, major section |
| H3 | `text-[18px] leading-[26px]` | 700 | Card title |
| H4 | `text-[16px] leading-[24px]` | 700 | Section title |
| Metric | `text-[28px] leading-[34px]` | 700 | KPI number |
| Body | `text-[14px] leading-[22px]` | 400 | Body copy |
| BodyMedium | `text-[14px] leading-[22px]` | 500 | Values, row labels |
| BodyStrong | `text-[14px] leading-[22px]` | 600 | Label, table title |
| Caption | `text-[12px] leading-[16px]` | 400 | Metadata/helper |
| CaptionStrong | `text-[12px] leading-[16px]` | 600 | Badge/table header |
| Micro | `text-[11px] leading-[14px]` | 500 | Small metadata |
| Button | `text-[14px] leading-[20px]` | 600 | Button labels |

### 3.4 Spacing scale

Use multiples of 4.

| Token | Value | Usage |
|---|---:|---|
| `space-1` | 4px | icon micro gap |
| `space-2` | 8px | icon-text gap |
| `space-3` | 12px | compact padding |
| `space-4` | 16px | default internal card gap |
| `space-5` | 20px | card padding |
| `space-6` | 24px | page/grid gap |
| `space-8` | 32px | modal section gap |
| `space-10` | 40px | auth/card large padding |
| `space-12` | 48px | hero spacing |
| `space-16` | 64px | large centered layout |

### 3.5 Radius scale

| Token | Value | Usage |
|---|---:|---|
| XS | 6px | tiny chip, table pill |
| SM | 8px | icon button |
| MD | 10px | nav item |
| LG | 12px | input/button |
| XL | 16px | card/dropdown |
| 2XL | 20px | modal/auth card |
| 3XL | 24px | large document viewer |
| Full | 9999px | avatar/pill |

---

## 4. Layout system

### 4.1 App shell

Use one shell for authenticated routes.

```tsx
<div className="min-h-screen bg-app text-default">
  <aside className="fixed inset-y-0 left-0 z-[var(--z-sidebar)] w-[var(--shell-sidebar-w)] border-r border-subtle bg-sidebar">
    <Sidebar />
  </aside>

  <header className="fixed left-[var(--shell-sidebar-w)] right-0 top-0 z-[var(--z-topbar)] h-[var(--shell-topbar-h)] border-b border-subtle bg-surface">
    <Topbar />
  </header>

  <main className="ml-[var(--shell-sidebar-w)] pt-[var(--shell-topbar-h)]">
    <div className="min-h-[calc(100vh-var(--shell-topbar-h))] px-6 py-6">
      {children}
    </div>
  </main>
</div>
```

Rules:

- Sidebar is fixed, not re-rendered differently per route.
- Topbar is fixed and uses one global search component.
- Content area scrolls; sidebar/topbar remain stable.
- Footer disclaimer is part of content template, not absolute to body unless page is short.
- Never draw dark vertical shell borders. Use `border-subtle`.

### 4.2 Desktop page templates

#### Template A — Main + right rail

Use for Patients and Documents.

```txt
Page
├─ PageHeader
├─ Grid: columns [main minmax(0, 1fr)] [rail 360px/392px]
│  ├─ MainColumn
│  └─ RightRail
└─ FooterDisclaimer
```

CSS:

```tsx
<div className="grid grid-cols-[minmax(0,1fr)_392px] gap-6">
  <section className="min-w-0 space-y-4">{main}</section>
  <aside className="space-y-4">{rail}</aside>
</div>
```

#### Template B — Chat + rail

```tsx
<div className="grid min-h-[calc(100vh-var(--shell-topbar-h)-48px)] grid-cols-[minmax(680px,1fr)_420px] gap-8">
  <section className="relative flex min-w-0 flex-col">
    <ChatThread />
    <ChatComposer className="sticky bottom-6 mt-auto" />
  </section>
  <aside className="space-y-4">
    <HowItWorksCard />
    <GeneralKnowledgeCard />
  </aside>
</div>
```

Rules:

- Suggestion chips live above composer or inside thread header, never floating unanchored.
- Safe refusal card is a `Chat/AnswerCard` variant, not a random card.
- Composer width must match thread column.

#### Template C — Dashboard

```txt
Dashboard
├─ PageHeader + actions
├─ MetricRow / or ErrorState
├─ 2-column cards
├─ Charts row
└─ FooterDisclaimer
```

If API fails, do not render a blank page. Use:

```tsx
<DashboardErrorState
  title="Unable to load dashboard"
  description="We could not fetch dashboard metrics. Check API connection or retry."
  primaryAction="Retry"
  secondaryAction="View logs"
/>
```

#### Template D — Auth split

```tsx
<div className="grid min-h-screen grid-cols-[45%_55%] bg-page">
  <AuthMarketingPane />
  <AuthFormPane />
</div>
```

Rules:

- Login card sits in right pane center.
- Background image is decorative only.
- Form inputs must be on opaque or near-opaque surface.

---

## 5. Brand and logo system

### 5.1 Required `BrandLockup`

The current screenshots show logo distortion and invisibility. Replace every logo usage with one component.

```tsx
type BrandLockupProps = {
  variant?: "sidebar" | "topbar" | "auth";
  showSubtitle?: boolean;
};
```

Sizing:

| Variant | Logo tile | Title | Subtitle |
|---|---:|---|---|
| sidebar | 40×40 | `Hospital AI` / `text-[14px] font-semibold` | `Knowledge Assistant` / `text-[11px]` |
| topbar | 36×36 | `AI-Powered Hospital Knowledge Assistant` / `text-[16px] font-semibold` | none |
| auth | 60×60 | Product title / `H3` | optional subtitle |

Implementation rules:

```txt
- Logo file must be SVG when possible.
- If PNG: use width/height fixed and `object-contain`.
- Do not use CSS background-size cover for logo.
- Put logo inside white tile only if image needs contrast.
- Use accessible label: aria-label="AI-Powered Hospital Knowledge Assistant".
- If logo asset fails: fallback to ShieldCheck + Cross icon.
```

Example:

```tsx
<div className="flex h-[58px] items-center gap-3">
  <div className="grid size-10 place-items-center rounded-lg bg-white shadow-sm ring-1 ring-border-default">
    <img src="/brand/hospital-ai-logo.svg" alt="" className="size-8 object-contain" />
  </div>
  <div className="min-w-0">
    <p className="truncate text-[14px] font-semibold leading-5 text-strong">Hospital AI</p>
    <p className="truncate text-[11px] leading-4 text-muted">Knowledge Assistant</p>
  </div>
</div>
```

---

## 6. shadcnUI component rules

### 6.1 Button

Base: `components/ui/button.tsx`

Variants:

```txt
primary, secondary, outline, ghost, link, destructive
sizes: sm 32, md 40, lg 48, icon 36/40
```

Class contract:

```txt
primary: bg-primary-600 text-white hover:bg-primary-700
secondary/outline: bg-white border border-default text-strong hover:border-strong hover:bg-primary-50
ghost: bg-transparent text-primary-600 hover:bg-primary-50
destructive: bg-danger-100 text-danger-700 hover:bg-danger-50
focus: focus-visible:ring-[3px] focus-visible:ring-primary-600/12
disabled: opacity-50 cursor-not-allowed
```

### 6.2 Input / Select

Base: shadcn `Input`, `Select`, `Textarea`.

Default:

```txt
height 44/48
radius LG
bg white
border default
text body
placeholder text-subtle
```

States:

```txt
hover: border-strong
focus: border-focus + focus-ring
error: border-danger-600 + helper danger
disabled: bg-surface-tint opacity 70
```

### 6.3 Card

Base: shadcn `Card`

```tsx
<Card className="rounded-xl border border-default bg-surface shadow-card">
```

Rules:

- Page cards use `radius-xl`.
- Auth card uses `radius-2xl`.
- Error card uses semantic left accent or icon, not full red box.
- Do not use dark navy border except selected/high-emphasis clinical state.

### 6.4 Badge / Chip

Use `Badge` for small status.

| Tone | Background | Text | Examples |
|---|---|---|---|
| success | `success-100` | `success-700` | Active, Indexed, Verified |
| danger | `danger-100` | `danger-700` | Denied, Failed |
| warning | `warning-100` | `warning-700` | Needs review |
| primary | `primary-100` | `primary-700` | Selected, Inpatient |
| purple | `purple-100` | `purple-600` | AI Assistant |
| neutral | `surface-tint` | `muted` | Archived |

### 6.5 Dropdown menu

Current screenshot issue: dropdown feels unanchored and overlaps unrelated controls.

Use shadcn/Radix correctly:

```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <button className="...">...</button>
  </DropdownMenuTrigger>

  <DropdownMenuContent
    align="end"
    sideOffset={8}
    collisionPadding={16}
    className="
      z-[var(--z-dropdown)]
      w-64 rounded-xl border border-default bg-surface
      p-2 text-default shadow-popover
      data-[side=bottom]:animate-in
    "
  >
    ...
  </DropdownMenuContent>
</DropdownMenu>
```

Rules:

```txt
- Always render through Portal (shadcn default).
- Surface must be opaque white. Do not use blur for this menu.
- Menu item height: 40px.
- Destructive item is separated by `Separator` and uses danger token.
- Dropdown content must not include page-level Filter button.
- Page filter popover and user dropdown are different components.
```

### 6.6 Dialog / Modal

Use shadcn `Dialog`.

```txt
Backdrop: bg-overlay
Content: bg-surface, radius-2xl, shadow-modal
z-index: modal 600
Focus trap: required
Close button: top-right
```

### 6.7 Table

Use shadcn `Table`, but create domain wrappers.

```txt
Table container: card, overflow-hidden
Header: sticky top-0 bg-surface-tint
Row height: 56px normal, 48px compact
Cell padding: 12–16
Divider: border-subtle
Actions: right-aligned icon button
```

Documents table must not grow beyond viewport without scroll.

```tsx
<div className="max-h-[520px] overflow-auto rounded-xl border border-default bg-surface">
  <Table>...</Table>
</div>
```

---

## 7. Domain components

### 7.1 AppShell

```txt
components/layout/AppShell.tsx
components/layout/Sidebar.tsx
components/layout/Topbar.tsx
components/layout/BrandLockup.tsx
components/layout/UserMenu.tsx
components/layout/GlobalSearch.tsx
```

Acceptance criteria:

- One sidebar width across app.
- One topbar height across app.
- Search centered but not pushing user trigger out.
- Topbar user trigger is always right-aligned.
- User menu content aligns to trigger right edge.

### 7.2 Auth

```txt
components/auth/AuthSplitLayout.tsx
components/auth/AuthMarketingPane.tsx
components/auth/LoginCard.tsx
components/auth/AuthTrustStrip.tsx
```

Login screenshot fix:

```txt
- Left pane: product value proposition + security bullets.
- Right pane: clean form surface.
- Background image: decorative, masked, not under input text.
- Login card: 520–576px width desktop, centered vertically.
- Form submit disabled state visible but not confusing.
```

Recommended auth background layering:

```tsx
<div className="relative overflow-hidden bg-[linear-gradient(135deg,#F7FAFF_0%,#FFFFFF_55%,#EAF2FF_100%)]">
  <img
    src="/assets/hospital-team-bg.png"
    className="absolute inset-y-0 right-0 h-full w-[70%] object-cover opacity-20"
    alt=""
  />
  <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-white/70" />
  <div className="relative z-10 grid min-h-screen place-items-center">
    <LoginCard />
  </div>
</div>
```

### 7.3 Patients page

```txt
components/patients/PatientSearchToolbar.tsx
components/patients/PatientListRow.tsx
components/patients/RecentPatientsRail.tsx
components/patients/QuickStatsCard.tsx
```

Layout:

```tsx
<div className="grid grid-cols-[minmax(0,1fr)_392px] gap-6">
  <main className="space-y-4">
    <PatientSearchToolbar />
    <PatientList />
  </main>
  <aside className="space-y-4">
    <RecentPatientsRail />
    <QuickStatsCard />
  </aside>
</div>
```

Rules:

- Search and filters stay inside `PatientSearchToolbar`.
- Patient rows use one consistent card row component.
- Status chip right aligned.
- Recent Patients card uses same patient row mini variant.

### 7.4 Chat page

```txt
components/chat/ChatLayout.tsx
components/chat/ChatSafeRefusalCard.tsx
components/chat/ChatComposer.tsx
components/chat/HowItWorksCard.tsx
components/chat/GeneralKnowledgeToggleCard.tsx
```

Safe refusal card content:

```txt
Title: Cannot answer this question
Reason: Insufficient clinical evidence available.
Alternatives:
- Try a more specific query
- Check if relevant documents are indexed
- Consult a senior physician
```

Rules:

- Safe refusal card max width `720px`.
- Icon tile sits aligned to message card top, not floating far left.
- Composer max width equals thread content width.
- Right rail cards fixed width `420px`.

### 7.5 Documents page

```txt
components/documents/DocumentUploadDropzone.tsx
components/documents/DocumentsTable.tsx
components/documents/SemanticSearchCard.tsx
components/documents/StorageUsageCard.tsx
```

Layout:

```tsx
<div className="grid grid-cols-[minmax(0,1fr)_360px] gap-6">
  <main className="min-w-0 space-y-4">
    <DocumentSearchBar />
    <DocumentUploadDropzone />
    <DocumentsTable />
  </main>
  <aside className="space-y-4">
    <SemanticSearchCard />
    <StorageUsageCard />
  </aside>
</div>
```

Fixes:

- Remove dark shell borders.
- Use `border-dashed border-default` on dropzone, not navy.
- Table uses sticky header and `max-h` scroll.
- Dates should be formatted human-readably, not raw ISO with long decimals.

### 7.6 Dashboard error/empty

```txt
components/empty/DashboardErrorState.tsx
components/empty/DashboardSkeleton.tsx
components/empty/EmptyStateCard.tsx
```

Dashboard failed fetch must render this:

```tsx
<Card className="mx-auto mt-6 max-w-3xl border-danger-100 bg-surface p-8 text-center shadow-card">
  <AlertTriangle className="mx-auto size-10 text-danger-600" />
  <h2 className="mt-4 text-[18px] font-semibold text-strong">Unable to load dashboard</h2>
  <p className="mt-2 text-sm text-muted">Failed to fetch dashboard summary. Check API connection or retry.</p>
  <div className="mt-6 flex justify-center gap-3">
    <Button>Retry</Button>
    <Button variant="outline">View logs</Button>
  </div>
</Card>
```

---

## 8. Page-specific repair checklist

### 8.1 `/login`

- [ ] Replace broken logo with `BrandLockup variant="auth"`.
- [ ] Split screen into marketing pane and form pane.
- [ ] Mask hospital/doctor background behind a gradient scrim.
- [ ] Keep login card on opaque/near-opaque surface.
- [ ] Button disabled style must still be legible.
- [ ] Inputs use icon-left and correct focus state.
- [ ] Trust strip chips align horizontally and fit inside card.

### 8.2 `/patients`

- [ ] Use `PageGrid main + rail`.
- [ ] Move page filter button/popover out of user dropdown layer.
- [ ] Right rail cards align to top of main list area.
- [ ] Recent patient mini rows use avatar + name + MRN/department.
- [ ] Patient row status chip uses `success` tone.
- [ ] Sort icon is aligned inside row action area.
- [ ] User dropdown does not cover or blur page controls unless opened intentionally.

### 8.3 `/chat/new`

- [ ] Suggestion chips align above conversation or composer.
- [ ] Safe refusal card uses `ChatSafeRefusalCard`.
- [ ] Composer is sticky bottom inside thread column.
- [ ] Right rail has `How it works` + `General Medical Knowledge`, same card width.
- [ ] Empty top whitespace reduced; content starts at page header y + 24/32.

### 8.4 `/documents`

- [ ] Remove dark borders around shell/sidebar/topbar.
- [ ] Use `DocumentsGrid`.
- [ ] Upload dropzone dashed border uses `border-default`.
- [ ] Table max height and sticky header prevent clipping.
- [ ] Format indexed date as `Jun 11, 2026, 03:54` or similar.
- [ ] Storage card chart center and label align.

### 8.5 `/dashboard`

- [ ] Replace raw red error text with `DashboardErrorState`.
- [ ] On loading, render skeleton metrics/cards.
- [ ] On empty data, render onboarding empty state.
- [ ] On success, render KPI/cards/charts.
- [ ] Use `ErrorBoundary` around dashboard data widgets.

---

## 9. Accessibility rules

- Every interactive item must be reachable with keyboard.
- Focus style: `outline: none; box-shadow: var(--effect-focus-ring); border-color: var(--color-border-focus)`.
- Dropdown and dialog must return focus to trigger on close.
- Form inputs must have visible labels, not placeholder-only labels.
- Icon-only buttons need `aria-label`.
- Decorative images use `alt=""`.
- Clinical warning/refusal/error text must not rely on color only; include icon + label.

---

## 10. Data and content formatting

### Dates

Never show raw ISO strings like:

```txt
2026-06-11T03:54:51.874851
```

Use:

```txt
Jun 11, 2026, 03:54
```

or in Vietnamese UI:

```txt
11/06/2026 03:54
```

### IDs

MRN text:

```txt
MRN: MRN-2024-0001 · Cardiology
```

Long UUIDs in tables should be truncated with tooltip.

### Error copy

Bad:

```txt
Failed to fetch
```

Good:

```txt
Unable to load dashboard
We could not fetch dashboard metrics. Check your API connection or retry.
```

---

## 11. Implementation file structure

```txt
src/
  app/
    globals.css
    login/page.tsx
    login/mfa/page.tsx
    (app)/
      layout.tsx
      dashboard/page.tsx
      patients/page.tsx
      chat/new/page.tsx
      documents/page.tsx

  components/
    ui/                       # shadcnUI primitives
      button.tsx
      card.tsx
      input.tsx
      dropdown-menu.tsx
      dialog.tsx
      table.tsx
      badge.tsx
      avatar.tsx
      separator.tsx
      skeleton.tsx
      switch.tsx

    layout/
      AppShell.tsx
      Sidebar.tsx
      Topbar.tsx
      BrandLockup.tsx
      GlobalSearch.tsx
      UserMenu.tsx
      EnvironmentPill.tsx

    auth/
      AuthSplitLayout.tsx
      AuthMarketingPane.tsx
      LoginCard.tsx
      AuthTrustStrip.tsx

    patients/
      PatientSearchToolbar.tsx
      PatientListRow.tsx
      PatientList.tsx
      RecentPatientsRail.tsx
      QuickStatsCard.tsx

    chat/
      ChatLayout.tsx
      ChatSafeRefusalCard.tsx
      ChatComposer.tsx
      HowItWorksCard.tsx
      GeneralKnowledgeToggleCard.tsx

    documents/
      DocumentUploadDropzone.tsx
      DocumentsTable.tsx
      SemanticSearchCard.tsx
      StorageUsageCard.tsx

    empty/
      DashboardErrorState.tsx
      EmptyStateCard.tsx
      SkeletonMetricCard.tsx

  lib/
    cn.ts
    format.ts
    constants.ts
```

---

## 12. Visual QA acceptance gates

### Global

- [ ] No broken/cropped logo in any route.
- [ ] No navy/black shell border unless intentionally selected/focused.
- [ ] Sidebar active item is consistent on all routes.
- [ ] Topbar search, environment pill, and user trigger are aligned.
- [ ] User dropdown aligns to trigger and overlays cleanly.
- [ ] All overlays appear above cards and below modal/toast.
- [ ] No page content is hidden behind topbar/sidebar.
- [ ] Body background is `bg-app`.

### Component-level

- [ ] Button variants match token states.
- [ ] Input default/focus/error states are distinct.
- [ ] Cards use consistent radius/border/shadow.
- [ ] Badges use semantic tone tokens.
- [ ] Table rows do not overflow horizontally without scroll.
- [ ] Empty/error states include next action.

### Page-level

- [ ] `/login` form readable over background.
- [ ] `/patients` main/rail columns align.
- [ ] `/chat/new` composer aligns with thread column.
- [ ] `/documents` table and rail fit viewport.
- [ ] `/dashboard` fetch error is actionable.

---

## 13. Agent execution prompt

Use this prompt with your coding agent:

```txt
You are fixing the HMS AI Copilot frontend UI. Read `hms-frontend-ui-fix-design-system.md` first and treat it as the UI repair contract.

Goal:
- Do not redesign randomly.
- Convert current UI to a consistent shadcnUI-based design system.
- Fix broken logo, auth background layering, dropdown/z-index, app shell alignment, page grids, borders, and dashboard error state.

Execution order:
1. Update globals.css with tokens from the design system.
2. Build/fix BrandLockup, AppShell, Sidebar, Topbar, UserMenu, EnvironmentPill.
3. Ensure DropdownMenu uses Portal, align=end, sideOffset=8, z-index dropdown, opaque bg-surface, shadow-popover.
4. Fix /login using AuthSplitLayout and masked background image.
5. Fix /patients using PageGrid main+rail and Patient components.
6. Fix /chat/new using ChatLayout and sticky composer.
7. Fix /documents using DocumentsGrid, subtle borders, sticky table header, formatted dates.
8. Fix /dashboard error/loading/empty/success states.
9. Remove hardcoded colors and replace with CSS variables/Tailwind tokens.
10. Run build/lint/tests and visually compare to screenshots.

Acceptance:
- No cropped logo.
- No dark shell borders.
- Dropdown is anchored and crisp.
- Login form is readable and not fighting the hospital image.
- All pages use shared components, not one-off shapes.
```

---

## 14. Done definition

The UI repair is complete when:

```txt
- `npm run build` passes.
- No TypeScript errors.
- No hardcoded hex colors in components except token definitions.
- All app routes render without crash.
- Screenshot comparison passes for login, patients, chat, documents, dashboard.
- Keyboard focus is visible in login, topbar search, dropdown menu, filters, composer.
- Error/empty/loading states are designed, not raw text.
```
