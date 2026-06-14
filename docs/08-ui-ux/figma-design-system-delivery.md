# Figma Design System Delivery Record

**Date:** June 8, 2026  
**Status:** Completed  
**Version:** 1.0  
**Target Figma File:** `RnOWTUhlXXie7AO24zggMm` (Page: `🎨 Design System`)

This document records the programmatic construction and alignment of the Design Tokens and Styles inside Figma using the `figma-mcp-go` tool.

---

## 1. Variable Tokens

We created a new variable collection called **`HMS Tokens`** containing standard layout measurements:

### Spacing Scale
- `Spacing/1` = `4px` (Micro gap)
- `Spacing/2` = `8px` (Icon-text / small chip padding)
- `Spacing/3` = `12px` (Compact table padding)
- `Spacing/4` = `16px` (Card internal / row gap)
- `Spacing/5` = `20px` (Compact card padding)
- `Spacing/6` = `24px` (Standard card/page gap)
- `Spacing/8` = `32px` (Modal / large section padding)
- `Spacing/10` = `40px` (Hero spacing)
- `Spacing/12` = `48px` (Auth layout spacing)
- `Spacing/16` = `64px` (Large centered spacing)

### Radius Scale
- `Radius/XS` = `6px` (Tiny chip / table pill)
- `Radius/SM` = `8px` (Icon button / badge)
- `Radius/MD` = `10px` (Sidebar nav item)
- `Radius/LG` = `12px` (Inputs / buttons / small cards)
- `Radius/XL` = `16px` (Major cards / dropdowns)
- `Radius/2XL` = `20px` (Modals / auth cards)
- `Radius/3XL` = `24px` (Large document viewer)
- `Radius/Full` = `999px` (Avatars / pills)

---

## 2. Paint Styles (Colors)

We renamed and updated existing color styles to match the singular `Color/` naming convention and created all missing color styles:

| Style Group | Style Token | Hex Value | Usage |
|---|---|---|---|
| **Background & Canvas** | `Color/Bg/App` | `#F7FAFF` | Soft blue-white canvas bg |
| | `Color/Bg/Page` | `#FFFFFF` | Main page background |
| | `Color/Bg/Surface` | `#FFFFFF` | Card, modal, drawer, table |
| | `Color/Bg/SurfaceTint` | `#F9FBFF` | Tinted empty state / inner panel |
| | `Color/Bg/Sidebar` | `#FAFCFF` | Sidebar background |
| | `Color/Bg/Overlay` | `#0F172A` | Backdrop for modals |
| **Borders** | `Color/Border/Subtle` | `#EEF3FB` | Light divider |
| | `Color/Border/Default` | `#DCE6F7` | Card, input, table borders |
| | `Color/Border/Strong` | `#BFD0EE` | Hover/focus borders |
| | `Color/Border/Focus` | `#2F7AF7` | Selected items border |
| **Typography** | `Color/Text/Strong` | `#081A48` | Titles & metrics |
| | `Color/Text/Default` | `#24365F` | Main body copy |
| | `Color/Text/Muted` | `#5B6B92` | Metadata & timestamps |
| | `Color/Text/Subtle` | `#8A98B8` | Placeholders |
| | `Color/Text/Inverse` | `#FFFFFF` | Contrast text on dark colors |
| | `Color/Text/Link` | `#0B5CDF` | Inline links & citations |
| **Brand & UI** | `Color/Primary/700` | `#004EC2` | Active/pressed state |
| | `Color/Primary/600` | `#0B5CDF` | Primary actions & links |
| | `Color/Primary/500` | `#2F7AF7` | Icon accent / focus |
| | `Color/Primary/300` | `#8BB8FF` | Illustration highlights |
| | `Color/Primary/100` | `#EAF2FF` | Selected option background |
| | `Color/Primary/50` | `#F5F9FF` | Light blue panels |
| **Semantics** | `Color/Success/700` | `#087443` | Success text |
| | `Color/Success/600` | `#12A763` | Success icon / positive |
| | `Color/Success/100` | `#E8F8EF` | Authorized chip bg |
| | `Color/Success/50` | `#F2FBF6` | Success card tint |
| | `Color/Danger/700` | `#B42318` | Denied / error text |
| | `Color/Danger/600` | `#EF4444` | Error icon |
| | `Color/Danger/100` | `#FFF1F1` | Error chip bg |
| | `Color/Warning/700` | `#B54708` | Warning text |
| | `Color/Warning/500` | `#F59E0B` | OCR processing |
| | `Color/Warning/100` | `#FFF6E5` | Warning chip bg |
| | `Color/Purple/600` | `#7C3AED` | AI/Refusal accent |
| | `Color/Purple/100` | `#F1E9FF` | AI chip bg |
| | `Color/Cyan/600` | `#0EA5B7` | Department accent |
| | `Color/Cyan/100` | `#E6FAFC` | Cyan tile bg |
| **Data Graph** | `Color/Chart/Blue` | `#1265F0` | Primary metric lines / bars |
| | `Color/Chart/Green` | `#18A957` | Positive trend |
| | `Color/Chart/Orange` | `#FF6B00` | Warning trend |
| | `Color/Chart/Purple` | `#7C3AED` | Secondary metrics / query volume |
| | `Color/Chart/Grid` | `#E7EDF8` | Grid lines |
| | `Color/Chart/Axis` | `#6B7898` | Labels |

---

## 3. Typography Presets

We aligned typography styles with clean names and font specifications:

- `Typography/Display` — `34px` / line `42px` (Bold/700)
- `Typography/H1` — `28px` / line `36px` (Bold/700)
- `Typography/H2` — `22px` / line `30px` (Bold/700)
- `Typography/H3` — `18px` / line `26px` (Bold/700)
- `Typography/H4` — `16px` / line `24px` (Bold/700)
- `Typography/Metric` — `28px` / line `34px` (Bold/700)
- `Typography/Body` — `14px` / line `22px` (Regular/400)
- `Typography/BodyMedium` — `14px` / line `22px` (Medium/500)
- `Typography/BodyStrong` — `14px` / line `22px` (SemiBold/600)
- `Typography/Caption` — `12px` / line `16px` (Regular/400)
- `Typography/CaptionStrong` — `12px` / line `16px` (SemiBold/600)
- `Typography/Micro` — `11px` / line `14px` (Medium/500)
- `Typography/Button` — `14px` / line `20px` (SemiBold/600)

---

## 4. Effect Styles (Shadows & Outlines)

We created standard depth effects for elevation and focus states:

- **`Effect/Shadow/Card`**: drop shadow `0 8px 24px` with color `#142650` (8% opacity)
- **`Effect/Shadow/Modal`**: drop shadow `0 18px 50px` with color `#142650` (18% opacity)
- **`Effect/Shadow/Popover`**: drop shadow `0 12px 34px` with color `#142650` (16% opacity)
- **`Effect/FocusRing`**: outer focus ring `spread 3px` with color `#0B5CDF` (12% opacity)

---

## 5. Visual Presentation on Figma Canvas

All updates have been rendered visually on the `🎨 Design System` page:
- **Typography presets box**: Resized the container, aligned the naming of old presets, and added two new rows (`Typography/H4` and `Typography/BodyMedium`) bound to their respective styles.
- **Backgrounds & Borders category box**: Expanded the container to add visual swatches, token names, hex values, and description strings for the five newly added colors (`Color/Bg/Page`, `Color/Bg/Sidebar`, `Color/Bg/Overlay`, `Color/Border/Subtle`, and `Color/Border/Focus`).

