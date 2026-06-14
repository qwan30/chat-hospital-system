# Design System

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  
> Reference: `00_product_ui_truth.md`, `figma-design-system-delivery.md`, `hms-frontend-ui-fix-design-system.md`

## 1. Brand

Clean modern-SaaS clinical interface — white canvas, confident typography, clear hierarchy. Designed for fast clinical scanning with accessible contrast.

## 2. Colors

| Token | Hex | Use |
|-------|-----|-----|
| Primary | `#111111` | CTAs, headlines |
| Primary Hover | `#242424` | Button press |
| Canvas | `#ffffff` | Page background |
| Surface Tint | `#f8f9fa` | Section alternates |
| Surface Card | `#f5f5f5` | Cards, elevated |
| Hairline | `#e5e7eb` | Borders, dividers |
| Surface Dark | `#101010` | Footer only |
| Text Default | `#111111` | Headlines |
| Text Body | `#374151` | Body copy |
| Text Muted | `#6b7280` | Secondary, captions |
| Text Subtle | `#898989` | Tertiary, placeholders |
| Success | `#10b981` | Confirmation, indexed |
| Warning | `#f59e0b` | Processing |
| Error | `#ef4444` | Failures, denials |
| Info | `#3b82f6` | Links |

## 3. Typography

| Level | Size | Weight | Use |
|-------|------|--------|-----|
| H1 | 36px | 600 | Page titles |
| H2 | 28px | 600 | Section headers |
| H3 | 22px | 600 | Card titles |
| H4 | 18px | 600 | Sub-headings |
| Body | 14px | 400 | Default text |
| Caption | 12px | 500 | Labels, badges |
| Button | 14px | 600 | CTAs |

Font: **Inter**, fallback to system sans-serif.

## 4. Spacing

`xs: 4px · sm: 8px · md: 16px · lg: 24px · xl: 32px · 2xl: 48px · Section: 96px`

## 5. Border Radius

`sm: 6px · md: 8px (buttons/inputs) · lg: 12px (cards) · xl: 16px · pill: 9999px (badges) · full: 50% (avatars)`

## 6. Components (shadcn/ui)

30+ primitives: Button, Card, Input, Dialog, DropdownMenu, Avatar, Badge, Tabs, Sheet, Command, Popover, Select, Switch, Table, Tooltip, Skeleton, Checkbox, RadioGroup, Progress, Separator, Label, Textarea, Sonner.

## 7. States

Every component: Default · Hover · Active · Focused · Disabled · Loading (skeleton) · Empty · Error.

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Recreated from current frontend tokens + Figma specs |
