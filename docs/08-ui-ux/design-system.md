# UI/UX Design System

> Project: AI-Powered Hospital Knowledge Assistant  
> Project Code: HOSP-AI-001  
> Version: 2.0  
> Status: Draft  
> Owner: UX Lead / UI Designer  
> Last Updated: 2026-06-07  

---

## 1. Design Philosophy & Guidelines

The user interface of the Hospital Knowledge Assistant (HOSP-AI-001) is designed around clinical efficiency, security transparency, and visual density (derived from modern workspace systems like Linear and Notion).

*   **Chat-First Workspace**: The primary entry screen lands the user directly in the chat interface (based on the Kotaemon workspace structure). Dashboard charts or configuration pages are secondary surfaces.
*   **Context Gating**: The user's active context (general hospital knowledge vs. a specific patient) is always clearly displayed. Patient context changes trigger explicit authorization state changes in the UI.
*   **Traceability**: Every claim made by the AI model is backed by inline citation chips. Clicking a citation opens a side panel rendering the raw source chunk/page summary.
*   **Accessibility (WCAG AA)**: Color is never used as the sole indicator of status (e.g., warnings have distinct symbols, active items have background fills and borders). High contrast and full keyboard navigation focus states are required.

---

## 2. Design Tokens

| UI Category | Token Name | Token Hex Value | Visual Use Case |
|---|---|---|---|
| **Background** | `bg.app` | `#08090a` | Main application viewport backdrop. |
| **Surface** | `surface.shell` | `#0f1011` | Sidebar, header bar, and prompt panels. |
| **Elevated** | `surface.elevated` | `#17181a` | Chat message bubbles, modals, drop-down menus. |
| **Border** | `border.subtle` | `#26282c` | Panel separators and list item grids. |
| **Primary Text** | `text.primary` | `#f7f8f8` | Primary clinical headers and copy text. |
| **Secondary Text** | `text.secondary` | `#a3a7ad` | Body text, labels, and description text. |
| **Muted Text** | `text.muted` | `#6f747d` | Timestamps, disabled placeholders, and minor info. |
| **Accent Primary**| `accent.primary` | `#5e6ad2` | Call-to-action buttons, active sidebar highlights. |
| **Info Accent** | `semantic.info` | `#60a5fa` | Citation highlights, general mode prompts. |
| **Success Status**| `semantic.success` | `#34d399` | Permission-allowed indicators, completed tasks. |
| **Warning Status**| `semantic.warning` | `#fbbf24` | Drug/allergy conflict notices, empty data warnings. |
| **Danger Status** | `semantic.danger` | `#f87171` | Access-denied blocks, system timeout failures. |

---

## 3. Screen Hierarchy & Wireframe Layouts

### Assistant Workspace Layout
```
+-------------------------------------------------------------------------------+
| App Logo | Attending Physician Name                       [Patient Context v] |
+-----------------------+----------------------------------+--------------------+
|                       |                                  |                    |
| (Sidebar)             | (Central Chat Area)              | (Evidence Panel)   |
|                       |                                  |                    |
| > New Chat            | Patient: John Doe (Allowed)      | Source Metadata:   |
|                       |                                  | file_signed.pdf    |
| - Allergy review      | User: What are his allergies?    | Page: 2            |
| - Prescription log    |                                  |                    |
| - Timeline notes      | AI: Patient is allergic to       | Excerpt:           |
|                       | Penicillin [1].                  | \"Patient reports  |
|                       |                                  | severe allergy     |
|                       | [1] Ingestion records            | to Penicillin      |
|                       |                                  | (anaphylaxis).\"   |
|                       |                                  |                    |
|                       +----------------------------------+                    |
|                       | Ask patient-scoped question...   |                    |
+-----------------------+----------------------------------+--------------------+
```

---

## 4. Core UI Component States

*   **Conversation Sidebar**:
    *   *Empty*: Shows instructions on starting a new chat thread.
    *   *Active Thread*: Border highlight (`border.subtle`) and fill (`surface.elevated`) with rename and share action controls visible on hover.
*   **Patient Context Gate**:
    *   *General Mode*: Icon: Blue Shield. Placeholder: "Ask about hospital policies..."
    *   *Patient Mode (Allowed)*: Icon: Green Lock. Displays patient MRN and name.
    *   *Patient Mode (Denied)*: Icon: Red Lock. Hides patient metrics, blocks input, and displays "Audit trail access violation logged."
*   **Citation Chip**:
    *   *Default*: Rendered as `[1]`, `#5e6ad2` font with small border.
    *   *Selected*: Inverse colors, highlighting the corresponding source chunk in the side panel.
    *   *Unavailable*: Muted text, indicating source files have been soft-deleted or archived.

---

## Change Log
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-04-28 | UX Designer | Initial UI layout rules |
| 2.0 | 2026-06-07 | Agent | Consolidated design tokens, visual workspace wireframe, and accessibility notes |
