# AI-Powered Hospital Knowledge Assistant
## Comprehensive UI/UX Reverse-Engineering and Product Design Specification

**Source:** visual analysis of seven supplied desktop screenshots  
**Reference viewport:** 1448 × 1086 px for every image  
**Product context:** clinician-facing hospital knowledge assistant using synthetic patient data  
**Document purpose:** consolidate the visible product structure, content, interaction states, design system, component inventory, and implementation guidance into one professional handoff document.

> **Accuracy note:** copy, numbers, filenames, statuses, and labels below are transcribed from the screenshots. Measurements, font families, and color hex values are inferred from pixels and should be treated as implementation approximations rather than original source-design tokens.

---

# 1. Product overview

The interface is a desktop clinical knowledge workspace designed to let authenticated clinicians:

- search patients, documents, guidelines, and prior conversations;
- ask patient-specific clinical questions;
- retrieve evidence with source citations;
- safely refuse unsupported questions rather than hallucinate;
- upload PDFs, images, TIFFs, and DICOM files;
- run OCR, chunking, embedding, and indexing pipelines;
- manually review low-confidence OCR output;
- inspect source integrity, permission status, and data sensitivity;
- request access to a protected patient record;
- review audit activity, metrics, timelines, and recent work.

The primary design principles visible throughout the set are:

1. **Clinical safety before answer completion.** Unsupported requests produce a clearly explained refusal with remediation actions.
2. **Permission-aware retrieval.** Authorization state is continuously visible, and denied access is handled through an auditable workflow.
3. **Traceable evidence.** Answers are connected to document-level and chunk-level citations.
4. **Human review for uncertain extraction.** Low OCR confidence blocks indexing until review.
5. **Operational transparency.** Upload, OCR, chunking, embedding, and indexing progress are exposed.
6. **Calm enterprise visual language.** White surfaces, dark navy text, restrained blue, semantic colors, subtle borders, and generous spacing.

---

# 2. Source-screen inventory

| Screenshot | Primary state |
|---|---|
| `chat.answer.safe-refusal-insufficient-evidence(3).png` | Patient chat produces a safe refusal because no authorized evidence directly answers the request. |
| `documents.dashboard.ocr-indexing-semantic-search(3).png` | Documents & OCR dashboard with upload entry points, filters, file table, semantic search, pipeline metrics, and storage usage. |
| `documents.ocr-review.needs-review-low-confidence(3).png` | Low-confidence OCR document-review workspace before indexing. |
| `documents.upload.batch-ocr-progress-modal(3).png` | Batch upload modal with per-file progress and pipeline stages. |
| `citations.viewer.verified-source-document(3).png` | Citation/source viewer showing the original document, extracted snippet, integrity, permissions, and PHI sensitivity. |
| `search.global.command-palette-recent-entities(4).png` | Global command palette with recent patients, documents, commands, and threads. |
| `access-requests.create.clinical-justification-modal(3).png` | Access-denied state with a structured patient-access request modal. |

---

# 3. Global information architecture

## 3.1 Top application bar

The top bar remains consistent across the screenshots.

### Left brand block

- Shield-style hospital logo with a white medical cross.
- Blue-to-teal gradient treatment.
- Two-line product name:
  - **AI-Powered Hospital**
  - **Knowledge Assistant**

### Global search

A large centered search field with:

- magnifying-glass icon;
- placeholder: **“Search patients, documents, guidelines, and more…”**;
- keyboard shortcut badge: **⌘K**.

The command-palette screenshot confirms this field opens a global search/command overlay.

### Environment and account controls

From left to right:

- green environment selector: **Synthetic Data**;
- shield/security icon;
- profile menu containing:
  - avatar;
  - **Dr. Sarah Chen**;
  - specialty: **Cardiology**;
  - dropdown chevron.

## 3.2 Primary sidebar

The persistent left navigation contains outline icons and these destinations:

1. Dashboard
2. Patients
3. Chat
4. Documents
5. Timeline
6. Audit
7. Metrics
8. Settings

### Selected state

The active section uses:

- pale blue rounded rectangle background;
- blue icon and text;
- no heavy border.

### Contextual recent-work module

The lower sidebar changes by section:

- **Chat:** Recent Threads and a **+ New** action.
- **Documents:** Recent Documents and a **+ Upload** action.
- **Patients:** Recent Patients and a **+ New** action.

### Permission card

A reusable green-accented card appears near the bottom:

- lock icon;
- title: **Permission-aware retrieval**;
- description: **“You have access to data for the selected patient.”**
- link: **Learn more**.

### Footer status

Bottom-left footer content:

- green status pill: **Audit ready**;
- **Last login: May 10, 2025, 8:51 AM**.

## 3.3 Global page footer

Centered along the bottom:

- **“AI can make mistakes. Verify important information.”**
- link: **Learn more**.

This creates a persistent clinical-safety reminder without overwhelming the main task area.

---

# 4. Inferred layout system

## 4.1 Desktop shell

Approximate geometry at the 1448 × 1086 reference size:

- top bar: about 80 px high;
- left sidebar: about 230–245 px wide;
- main content gutter: about 22–28 px;
- optional right rail: about 360–390 px wide;
- standard card gap: about 16 px;
- page bottom/status bar: about 36 px.

The content uses a 12-column-like desktop grid, but most screens resolve into one of three structures:

1. **Sidebar + broad main canvas + right evidence rail**
2. **Sidebar + full-width operational dashboard**
3. **Dimmed page + centered modal**

## 4.2 Card geometry

Common card styling:

- 10–14 px corner radius;
- 1 px cool-gray border;
- white or nearly white fill;
- little to no shadow on in-page cards;
- soft, broad shadow on modals;
- 16–24 px internal padding.

## 4.3 Modal geometry

The screenshots show three modal scales:

- command palette: medium-width, tall search overlay;
- access request: wide form modal with explanatory side rail;
- citation viewer: very wide document workspace;
- upload modal: wide operational table modal.

Shared modal behavior:

- centered on viewport;
- page backdrop dimmed with a cool navy/gray overlay;
- close icon in top-right;
- primary action anchored at bottom-right;
- clear visual hierarchy between title, helper copy, content, and footer actions.

---

# 5. Inferred visual design system

## 5.1 Color tokens

The following are approximate visual equivalents.

| Token | Approx. hex | Usage |
|---|---:|---|
| `ink-900` | `#0B1F46` | Page titles, primary body text, major labels |
| `ink-700` | `#334563` | Secondary text and metadata |
| `ink-500` | `#66758F` | Placeholder, helper, timestamps |
| `primary-600` | `#0867DF` | Primary buttons, active navigation, links |
| `primary-100` | `#EAF2FF` | Selected navigation, icon discs, focused surfaces |
| `success-600` | `#149B68` | Authorized, indexed, verified, completed |
| `success-100` | `#E9F8F1` | Success badges and cards |
| `purple-600` | `#7446E8` | Safe-refusal/evidence-safety state |
| `purple-100` | `#F1EDFF` | Safety icon background and external/source accents |
| `warning-600` | `#D98410` | Low confidence, OCR processing, needs review |
| `warning-100` | `#FFF4E4` | Warning badges and confidence chips |
| `danger-600` | `#D83E3E` | OCR failed, archive, access denied, destructive actions |
| `danger-100` | `#FFF0F0` | Error banners and failure badges |
| `border-200` | `#DDE5EF` | Borders, dividers, input outlines |
| `surface-50` | `#F7F9FC` | App canvas and subtle card backgrounds |
| `surface-0` | `#FFFFFF` | Primary cards and modal surfaces |

## 5.2 Typography

The type appears to be a modern humanist/geometric sans-serif similar to **Inter**, **SF Pro**, or **Manrope**.

Approximate scale:

| Role | Size | Weight |
|---|---:|---:|
| Product brand | 18–20 px | 650–700 |
| Page title | 24–28 px | 650–700 |
| Modal title | 22–26 px | 650–700 |
| Section title | 16–20 px | 650–700 |
| Standard body | 13–15 px | 400–500 |
| Control label | 12–13 px | 600 |
| Metadata/helper | 11–13 px | 400–500 |
| Badge | 10–12 px | 550–650 |

Line height is generous, typically around 1.4–1.55 for prose and 1.2–1.3 for controls.

## 5.3 Spacing

The interface strongly suggests a 4 px base grid:

- 4 px: micro gaps;
- 8 px: icon-to-text, badge padding;
- 12 px: compact row spacing;
- 16 px: standard component gap;
- 24 px: card padding and section separation;
- 32 px: page-section rhythm;
- 40–48 px: larger visual group separation.

## 5.4 Iconography

- predominantly outline icons;
- rounded stroke caps;
- 18–24 px standard size;
- icons placed inside pale tinted circles for high-priority actions or statuses;
- semantic color always paired with text, not used alone.

## 5.5 Borders and focus

- normal input border: cool gray;
- focus border: saturated blue, often with a subtle blue halo;
- selected radio/card option: 2 px blue outline plus a filled radio mark;
- destructive action: red icon/text, white background, red-tinted hover expected.

## 5.6 Shadows and overlays

- in-page surfaces use borders more than shadows;
- modals use a broad, low-opacity shadow;
- backdrop overlay is approximately 45–60% dark cool gray/blue;
- foreground modal remains bright white for strong depth separation.

---

# 6. Reusable component inventory

## 6.1 Navigation components

- brand lockup;
- primary nav item;
- selected nav item;
- recent-item row with icon, title, date/status;
- sidebar action button (`+ New`, `+ Upload`);
- permission-aware status card;
- bottom audit-status badge.

## 6.2 Button variants

### Primary

- saturated blue fill;
- white text and icon;
- examples: **Ask**, **Search**, **Approve & Index**, **Continue**, **Submit request**.

### Secondary

- white fill;
- gray/blue border;
- dark text;
- examples: **Generate Summary**, **Retry OCR**, **Edit Metadata**, **Cancel**.

### Destructive

- white fill;
- red text and red icon;
- example: **Archive**.

### Link button

- blue text;
- optional arrow/external-link icon;
- examples: **View details**, **See all results (12)**.

### Icon-only

- rounded square or plain icon;
- examples: filter, bookmark, overflow, close, page rotate, fullscreen.

## 6.3 Form controls

- text search input;
- multiline clinical-justification field with character count;
- dropdown/select fields;
- checkbox with confirmation copy;
- radio-card selection group;
- date/duration selector;
- urgency selector;
- relationship-to-patient selector;
- inline info icons for policy explanations.

## 6.4 Status and classification components

- Authorized;
- Indexed;
- OCR Processing;
- Archived;
- Index Failed;
- OCR Failed;
- Low confidence;
- Ready to index;
- Uploading;
- Needs review;
- Verified Source;
- Verified;
- PHI – High;
- External;
- Imaging;
- Clinical Note;
- Confidence: Low;
- Audit ready.

The status system uses both color and explicit labels.

## 6.5 Operational components

- upload drop zone;
- per-file progress bar;
- horizontal processing stepper;
- vertical timeline;
- document data table;
- pagination;
- thumbnail page rail;
- PDF/document canvas;
- extracted-text panel;
- issue-highlighting treatment;
- review checklist;
- storage donut chart;
- metric cards and trend charts.

## 6.6 Evidence components

- evidence empty state;
- retrieved-but-insufficient source card;
- citation/source viewer;
- extracted snippet card;
- relevance indicator dots;
- verification rows;
- source-integrity footer.

## 6.7 Safety components

- safe-refusal response card;
- low-confidence badge;
- permission-aware label;
- access-denied page;
- access-request workflow;
- audit-logging acknowledgement;
- global AI verification disclaimer.

---

# 7. Screen 1 — Safe Refusal / Insufficient Evidence

## 7.1 Screen purpose

Demonstrates the assistant declining to answer a clinical question when authorized evidence does not directly support an answer.

## 7.2 Page structure

- global top bar;
- Chat selected in sidebar;
- main conversation column;
- right Evidence & Citations rail;
- bottom composer and action controls.

## 7.3 Conversation header

Patient context chip:

- **Patient: Maria Gonzalez (MRN 103991)**

Authorization badge:

- **Authorized**

Thread title:

- **Safe Refusal / Insufficient Evidence**
- editable pencil icon;
- bookmark icon;
- overflow menu.

Metadata:

- **Today, 9:24 AM**
- **This thread is private to you** with lock icon.

## 7.4 User message

> What was the detailed MRI interpretation from the outside hospital last year?

Metadata:

- **9:24 AM**
- double-check/read indicator;
- user avatar initials: **SC**.

## 7.5 Assistant refusal card

Safety icon:

- purple shield with check mark inside a pale purple circle.

Heading:

- **Insufficient evidence**

Body copy:

> I'm unable to answer that question based on the available, authorized evidence.
>
> I did not find any MRI interpretation reports from the outside hospital last year in the accessible records. Generating an answer without supporting evidence could be inaccurate or misleading, so I won’t make unsupported claims.

Subheading:

- **What you can do next:**

Actions in copy:

- Search the knowledge base for MRI reports or outside records
- Upload the MRI report or related documents if you have them
- Ask a narrower question (e.g., date range, facility, or body region)

Boundary explanation:

> If you believe the document exists, it may be outside your current data access. Please request access or upload the document to proceed.

Safety footer:

- **Assistive output — verify with clinical staff.**
- orange badge: **Confidence: Low**
- info icon.

Response actions:

- thumbs up;
- thumbs down;
- copy;
- bookmark/save.

## 7.6 Suggested next-action cards

1. **Search documents**  
   Find relevant records

2. **Upload a document**  
   Add to knowledge base

3. **Ask a narrower question**  
   Refine your request

## 7.7 Composer

Placeholder:

- **Ask a clinical question or request information…**

Controls:

- send icon inside input;
- primary button: **Ask**;
- secondary button: **Generate Summary**;
- secondary button: **Safe. Refusal Test**;
- **Streaming** toggle, enabled.

## 7.8 Evidence & Citations rail

Header:

- **Evidence & Citations**
- green shield icon;
- subtitle: **Permission-aware results**;
- info icon;
- filter button.

Empty-state title:

- **No supporting evidence found**

Explanation:

> We couldn’t find any documents that directly answer your question in the authorized data you can access.

“What this means” card:

- The information may not exist in the accessible records.
- The document may be outside your data permissions.
- Try broadening your search or upload the document.

### Retrieved but insufficient — 2 results

#### Result 1

- **MRI Lumbar Spine Report (Outside Facility)**
- badge: **External**
- Captured: **Mar 12, 2024, 11:20 AM**
- Source: **External Documents**
- reason: **“This document appears related but does not contain the detailed interpretation requested.”**

#### Result 2

- **Radiology Report – Knee MRI**
- badge: **Imaging**
- Captured: **Jun 5, 2024, 9:14 AM**
- Source: **EHR – Imaging**
- reason: **“Different body region. Does not answer the question.”**

Bottom helper:

- **Can’t find what you need?**
- **“Upload the document or request access if you believe it exists but isn’t available.”**
- button: **Upload a document**.

## 7.9 Sidebar context

Recent Threads:

- Discharge summary — Today, 9:12 AM
- Lab result follow-up — May 9, 2:41 PM
- Patient summary — May 8, 10:03 AM
- View all threads

## 7.10 UX behavior inferred

- Retrieval executes only within the user’s authorized data scope.
- The assistant distinguishes “no result” from “related but insufficient.”
- Low confidence is explicitly surfaced.
- Recovery actions are available both inside the answer and as dedicated action cards.
- The refusal remains useful and actionable rather than stopping at a generic error.

---

# 8. Screen 2 — Documents & OCR Dashboard

## 8.1 Screen purpose

Central workspace for ingesting, processing, browsing, searching, and monitoring medical documents.

## 8.2 Header

Title:

- **Documents & OCR**

Subtitle:

- **Ingest, process, and search across structured and unstructured medical records.**

Documents is the selected sidebar item.

## 8.3 Upload entry area

Large dashed drop zone:

- upload-cloud icon;
- **Drag & drop files here, or choose an option below**
- **Supports PDF, PNG, JPG, TIFF, and DICOM**

Three actions:

1. **Upload PDF**
2. **Upload Image**
3. **Sync HMS Evidence**

## 8.4 Search and filters

Search placeholder:

- **Search documents by name, content, or patient…**

Filters:

- Patient
- Document Type
- Status
- Date
- Clear

Result count:

- **Showing 1–10 of 48 documents**

## 8.5 Document table

Columns:

- Document Name
- Patient
- Type
- Status
- OCR Confidence
- Indexed At
- Actions

All visible rows belong to **John Carter (MRN 104582)**.

| # | Document | Type | Status | OCR | Indexed at |
|---:|---|---|---|---:|---|
| 1 | Discharge Summary_2025-05-10.pdf | Discharge Summary | Indexed | 98% | May 10, 2025, 9:18 AM |
| 2 | Lab Results_2025-05-09.pdf | Lab Result | Indexed | 97% | May 9, 2025, 8:47 AM |
| 3 | Cardiology Consult Note_2025-05-08.pdf | Clinical Note | OCR Processing | 72% | May 8, 2025, 2:13 PM |
| 4 | Chest X-ray_2025-05-07.png | Imaging | Indexed | 94% | May 7, 2025, 11:02 AM |
| 5 | ECG Report_2025-05-06.pdf | ECG | Archived | 95% | May 6, 2025, 5:30 PM |
| 6 | Echocardiogram_2025-05-05.pdf | Imaging | Indexed | 96% | May 5, 2025, 10:11 AM |
| 7 | Operative Note_2025-05-04.pdf | Operative Note | Index Failed | — | May 4, 2025, 9:20 AM |
| 8 | Medication List_2025-05-03.pdf | Medication List | Indexed | 99% | May 3, 2025, 4:45 PM |
| 9 | Nursing Note_2025-05-02.pdf | Clinical Note | Indexed | 92% | May 2, 2025, 3:08 PM |
| 10 | Physiotherapy Note_2025-05-01.pdf | Clinical Note | Archived | 90% | May 1, 2025, 1:17 PM |

Each row ends with an overflow/action menu.

## 8.6 Pagination

Visible controls:

- previous arrow;
- pages 1, 2, 3, …, 5;
- page 1 selected;
- page-size selector: **10 / page**;
- **Go to page** field set to 1.

## 8.7 Semantic Search panel

Header:

- **Semantic Search** with info icon.

Query:

- **What medications is the patient currently taking?**

Primary action:

- **Search**

### Top matching chunks

#### 1. Medication List_2025-05-03.pdf — 98%

Snippet:

> … Lisinopril 10 mg PO daily … Metformin 500 mg PO BID … Atorvastatin 40 mg PO nightly … Aspirin 81 mg PO daily …

Metadata:

- Page 1
- Chunk 2
- May 3, 2025, 4:45 PM

#### 2. Discharge Summary_2025-05-10.pdf — 92%

Snippet:

> … Discharge medications reconciled: Lisinopril 10 mg daily, Metformin 500 mg BID, Atorvastatin 40 mg nightly, Aspirin 81 mg daily …

Metadata:

- Page 4
- Chunk 3
- May 10, 2025, 9:18 AM

#### 3. Cardiology Consult Note_2025-05-08.pdf — 88%

Snippet:

> … Recommend continue Lisinopril for BP control and Aspirin for secondary prevention …

Metadata:

- Page 2
- Chunk 1
- May 8, 2025, 2:13 PM

Link:

- **See all results (12)** with external/open icon.

## 8.8 Processing Pipeline panel

Pipeline stages:

1. Uploaded — Complete
2. OCR — Complete
3. Chunked — Complete
4. Embedded — Complete
5. Indexed — Complete

Summary metrics:

- **Today: 27 Uploaded**
- **Processing: 3 In Progress**
- **Failed: 1 Needs Review**
- **Indexed: 23 Completed**

## 8.9 Storage & Usage panel

Donut center:

- **62% Used**

Breakdown:

- Documents: **128 GB**
- Images: **84 GB**
- OCR Text: **46 GB**
- Embeddings: **32 GB**
- Other: **10 GB**

Totals:

- Total: **300 GB**
- Used: **186 GB**

## 8.10 Sidebar recent documents

- Discharge summary – J. Carter — May 10, 2025 — Indexed
- Lab results – John Carter — May 9, 2025 — Indexed
- Cardiology consult note — May 8, 2025 — OCR Processing
- Chest X-ray – 2025-05-07 — May 7, 2025 — Indexed
- ECG Report – 2025-05-06 — May 6, 2025 — Archived
- View all documents

## 8.11 UX behavior inferred

- Upload and existing-library management are kept on one page.
- Semantic retrieval is surfaced beside the document inventory, not hidden in a separate workflow.
- Processing health and capacity are visible at a glance.
- Status color and OCR confidence help prioritize manual review.
- Each document can likely be opened, reviewed, retried, archived, or otherwise managed via the overflow menu.

---

# 9. Screen 3 — Document Review / Low OCR Confidence

## 9.1 Screen purpose

Manual quality-control workspace for a document that failed OCR confidence requirements and is blocked from indexing.

## 9.2 Header and actions

Back link:

- **Back to Documents**

Title:

- **Document Review**

Subtitle:

- **Review and correct extracted content before indexing.**

Actions:

- **Retry OCR**
- **Edit Metadata**
- primary: **Approve & Index**
- destructive: **Archive**

## 9.3 Alert banner

Heading:

- **Low OCR confidence detected**

Body:

> This document could not be processed with sufficient accuracy. Please review the extracted text and metadata before indexing.

Controls:

- **Learn more**
- dismiss/close icon.

## 9.4 Document identity strip

Filename:

- **Outside_Referral_Scan_2025-05-11.pdf**

Status:

- **OCR Failed**

Patient:

- **Maria Gonzalez (MRN 103991)**

Upload time:

- **Uploaded May 11, 2025, 9:14 AM**

Document Type:

- **Referral Letter**
- inline action: **Change**

Uploaded:

- **May 11, 2025, 9:14 AM**

Source:

- **Referral Portal**

Overflow menu at far right.

## 9.5 Tabs

- Review — selected
- Metadata
- Activity

## 9.6 Review workspace

Three-column arrangement:

1. page thumbnails;
2. scanned document viewer;
3. extracted-text panel;

with a separate diagnostic rail on the far right.

### Page thumbnails

- header: **Pages (2)**
- page 1 selected with blue outline;
- page 2 unselected;
- action: **+ Add page**;
- footer: **2 pages total**.

### Document-viewer toolbar

- zoom out/search-like icon;
- zoom in icon;
- fit selector: **Fit**;
- previous page;
- page field: 1;
- total: / 2;
- next page;
- download icon;
- rotate/refresh icon.

### Scanned-document metadata

- **Scanned Document**
- **May 8, 2025**
- **300 DPI**

### Visible document content

Date:

- **May 8, 2025**

Recipient:

- Dr. Sarah Chen
- Cardiology Department
- Cityview Medical Center
- 123 Healthcare Way
- San Francisco, CA 94107

Patient reference:

- **RE: Maria Gonzalez (DOB: 07/14/1975)**
- **MRN: 103991**

Letter opening:

> Dear Dr. Chen,
>
> I am referring Ms. Maria Gonzalez for evaluation and management of progressive exertional dyspnea and occasional chest tightness.

History:

- 58-year-old female with history of hypertension and type 2 diabetes.
- Reports increasing shortness of breath over the past 6 months, now limiting daily activities.
- Occasional chest tightness with exertion, relieves with rest.
- Denies syncope, orthopnea, or PND.

Medications:

- Lisinopril 10 mg daily
- Metformin 500 mg BID
- Atorvastatin 20 mg nightly
- Aspirin 81 mg daily

Footer:

- **(continued)**

### Extracted Text panel

Header:

- **Extracted Text**
- badge: **Low confidence**
- info icon.

Search:

- **Search extracted text…**
- filter icon.

The extracted text mirrors the scan. Low-confidence/uncertain tokens are highlighted with a pale red background, including visible examples such as:

- Cardiology;
- San Francisco;
- MRN 103991;
- Lisinopril;
- Metformin.

Footer legend:

- **Low confidence / Uncertain**
- **12 issues found**.

## 9.7 Diagnostic rail

### Processing Timeline

- Uploaded — May 11, 2025, 9:14 AM
- Document validation — May 11, 2025, 9:14 AM
- OCR processing — May 11, 2025, 9:14 AM
  - Failed
  - Low confidence score
- Text extraction — Pending
- Indexing — Pending
- Complete — Pending
- link: **View full timeline**

### Failure Reasons

- Overall confidence below threshold (45%)
- Multiple illegible segments detected
- Uncertain text in critical fields
- Document quality may be poor
- link: **View details**

### Review Checklist

Progress:

- **0 of 4 completed**

Checklist:

1. Verify document type and metadata
2. Review and correct extracted text
3. Confirm medications and key data
4. Approve for indexing

Link:

- **View best practices**

## 9.8 Bottom guidance

Info bar:

> You can correct the extracted text, update metadata, and then approve for indexing. All changes are logged for audit and traceability.

Bottom-right:

- **Last updated: May 11, 2025, 9:14 AM**
- refresh icon.

## 9.9 UX behavior inferred

- The scan and extraction are displayed side by side to support line-by-line correction.
- Uncertain terms are visually highlighted rather than forcing users to search manually.
- Indexing is intentionally gated by a review checklist.
- Processing diagnostics explain why automation stopped.
- All edits are expected to generate audit events.

---

# 10. Screen 4 — Upload Documents & OCR Modal

## 10.1 Screen purpose

Batch file ingestion with live per-file upload/OCR status and an overall processing-stage model.

## 10.2 Modal header

Title:

- **Upload Documents & OCR**

Subtitle:

- **Upload files to extract text, structure data, and make content searchable.**

Icon:

- blue upload cloud in a pale circular background.

Close icon at top-right.

## 10.3 Drop zone

Copy:

- **Drag & drop files here, or browse**
- **Supports PDF, PNG, JPG, TIFF, and DICOM**

Button:

- **Browse files**

Limits:

- **Up to 50 files at a time**
- **Max 200 MB per file**

## 10.4 Selection summary

- **3 files selected (245.7 MB)**
- destructive link: **Remove all** with trash icon.

## 10.5 Batch table

Columns:

- File Name
- Patient
- Size
- Status
- Progress

### Row 1

- **Discharge_Summary_2025-05-10.pdf**
- type: Discharge Summary
- patient: John Carter / MRN 104582
- size: 2.4 MB
- status: **Ready to index**
- helper: **Completed**
- progress: **100%**
- green completed state and overflow menu.

### Row 2

- **Lab_Results_2025-05-09.pdf**
- type: Lab Result
- patient: John Carter / MRN 104582
- size: 12.8 MB
- status: **Uploading**
- helper: **Uploading to secure storage**
- progress: **65%**
- blue progress state and overflow menu.

### Row 3

- **Cardiology_Consult_Note_2025-05-08.pdf**
- type: Clinical Note
- patient: John Carter / MRN 104582
- size: 4.7 MB
- status: **Needs review**
- helper: **OCR confidence low**
- progress: **20%**
- orange warning state, warning icon, overflow menu.

## 10.6 Processing stepper

1. **Uploading** — Secure transfer — active
2. **OCR Parsing** — Extracting text
3. **Chunking** — Splitting content
4. **Embedding** — Generating vectors
5. **Ready to index** — Store & index

The active stage uses a filled blue node; later stages use empty outlined nodes.

## 10.7 Footer controls

Left:

- **+ Add more files**

Right:

- **Cancel**
- primary: **Continue** with arrow icon.

## 10.8 Security strip

Heading:

- **Secure ingestion & audit logging**

Body:

> All uploads are encrypted in transit and at rest. Access is role-based and fully audited.

System indicators:

- Audit logging: **Enabled**
- Data region: **US East (Ohio)**

## 10.9 UX behavior inferred

- Files can occupy different pipeline states concurrently.
- A failed/low-confidence file does not prevent other files from completing.
- The workflow explicitly communicates secure transfer and data residency.
- Users can add more files, remove all, inspect row actions, cancel, or continue.

---

# 11. Screen 5 — Citation Viewer / Verified Source Document

## 11.1 Screen purpose

Allows a clinician to inspect the exact source behind an answer, verify document provenance and permissions, and see the relevant extracted chunk.

## 11.2 Background chat context

Visible behind the modal:

- thread title: **Medication and allergy review**
- timestamp: **Today, 9:18 AM**
- **This thread is private to you**
- top action: **Sources (3)**
- user question: **“Summarize current allergies and any medication risks for this patient.”**
- user initials: **SC**

## 11.3 Modal header

Document:

- **Allergy_History_0424.pdf**
- badge: **Clinical Note**

Context:

- Patient: **John Carter (MRN 104582)**
- Source: **EHR – Allergies**

Actions:

- **Download PDF**
- **Open in Source**
- close icon.

## 11.4 Left page rail

- heading: **Pages**
- **2 pages**
- page 1 selected;
- page 2 available.

## 11.5 Document toolbar

- previous page;
- current page 1;
- total / 2;
- next page;
- zoom out;
- zoom level: **100%**;
- zoom in;
- fullscreen;
- search;
- rotate/reset-style icon.

## 11.6 Document content

Document branding:

- **General Hospital**
- tagline: **Care. Compassion. Excellence.**
- title: **Patient Allergy History**

Patient metadata:

- Patient Name: John Carter
- MRN: 104582
- DOB: May 14, 1962
- Date of Record: Apr 24, 2024, 8:41 AM
- Encounter Type: Office Visit
- Provider: Dr. Sarah Chen

### Allergies

- **Penicillin – rash (childhood)** — highlighted in yellow
- **Iodinated contrast – hives and pruritus**
- **No known food allergies**

### Allergy Details

#### Penicillin – rash (childhood)

> Patient reports rash after penicillin as a child. No history of anaphylaxis, angioedema, or respiratory compromise.

#### Iodinated contrast – hives and pruritus

> Developed hives and pruritus after iodinated contrast exposure in 2018. No respiratory compromise.

#### No known food allergies

> Patient denies any food allergies.

### Clinician Notes

- Documented by: Nurse Emily Johnson, RN
- Reviewed by: Dr. Sarah Chen, MD
- Record Status: Signed

## 11.7 Citation Details rail

Header:

- **Citation Details**
- badge: **Verified Source**
- info icon.

Fields:

- Document: Allergy_History_0424.pdf
- Page: 1
- Chunk: 2
- Captured: Apr 24, 2024, 8:41 AM
- Source: EHR – Allergies
- Accessed: May 10, 2025, 9:18 AM
- Accessed by: Dr. Sarah Chen

## 11.8 Extracted Snippet

Snippet:

> … Penicillin – rash (childhood) …  
> Iodinated contrast – hives and pruritus …  
> No known food allergies …

Relevance indicator:

- five-dot scale;
- four blue dots filled and one unfilled.

## 11.9 Verification section

- Source Integrity — **Verified**
- Permission Check — **Authorized**
- Data Sensitivity — **PHI – High**

## 11.10 Modal footer

Trust statement:

- **This document is from a trusted source and has not been altered.**

Link:

- **Learn more about our verification process**

## 11.11 UX behavior inferred

- Source provenance, access time, and user identity are audit-visible.
- The user can compare the original document with the extracted chunk.
- Source integrity and authorization are separate verification concepts.
- PHI classification is visible at point of use.
- “Open in Source” supports moving back to the system of record.

---

# 12. Screen 6 — Global Command Palette

## 12.1 Screen purpose

Fast keyboard-oriented navigation across entities and core product actions.

## 12.2 Search input

Placeholder:

- **Search patients, documents, threads, or commands…**

Shortcut:

- **⌘K**

The input has a visible blue focus outline and text caret.

## 12.3 Recent Patients

Header link:

- **View all patients**

Rows:

1. **John Carter (MRN 104582)**  
   63 y/o • Male • Cardiology

2. **Emily Davis (MRN 107331)**  
   54 y/o • Female • Endocrinology

3. **Michael Lee (MRN 102773)**  
   72 y/o • Male • Cardiology

Each row has:

- colored initials avatar;
- **Open**;
- Return/Enter-key indicator.

## 12.4 Recent Documents

Header link:

- **View all documents**

Rows:

1. **Discharge Summary_2025-05-10.pdf**  
   John Carter (MRN 104582) • Discharge Summary

2. **Lab Results_2025-05-09.pdf**  
   John Carter (MRN 104582) • Lab Result

3. **Cardiology Consult Note_2025-05-08.pdf**  
   John Carter (MRN 104582) • Clinical Note

Each row includes a PDF/file icon, **Open**, and Return/Enter indicator.

## 12.5 Quick Commands

1. **Start new clinical conversation**  
   Ask a question or get help with patient care  
   Shortcut: Return/Enter

2. **Generate patient summary**  
   Create an AI summary of patient data  
   Shortcut: Return/Enter

3. **Upload document**  
   Upload a file to add to the patient’s knowledge base  
   Shortcut: **⌘U**

4. **Open audit logs**  
   View audit events and access activity  
   Shortcut: **⌘⇧A**

5. **View metrics**  
   Explore performance, usage, and impact  
   Shortcut: **⌘⇧M**

## 12.6 Recent Threads

Header link:

- **View all threads**

Rows:

1. **Discharge summary for John Carter (MRN 104582)**  
   Today, 9:12 AM

2. **Lab result follow-up for Emily Davis (MRN 107331)**  
   May 9, 2:41 PM

3. **Anticoagulation guidance for Michael Lee (MRN 102773)**  
   May 9, 11:08 AM

Each row has **Open** and a Return/Enter indicator.

## 12.7 Keyboard tip

- **Tip: Use ↑↓ to navigate, ↵ to open, ⌘K to close**

## 12.8 Visible dashboard context behind overlay

The underlying Dashboard is dimmed but reveals:

- greeting: **Good morning, Dr. Sarah Chen 👋**;
- date range: **Apr 13 – May 10, 2025**;
- Filters control;
- Avg Lookup Time: **4.2 sec**;
- change: **↓ -76%** versus a baseline;
- Denied Audit Count: **2**;
- change: **↓ -60% vs. baseline (5)**;
- Answer Quality & Safety:
  - Retrieval Success Rate: **95.2%**;
  - Safe Refusals: **4.8%**;
  - period selector: **Daily**;
- User Feedback:
  - Average Rating: **4.7 / 5**;
  - **Based on 1,248 responses**;
  - visible feedback marked **Helpful**;
- visible feedback quotes:
  - “Saves me so much time finding the right policy or guideline. Citations help with confidence.” — Dr. Emily R., May 10, 2025
  - “The medication review is excellent. Catches interactions I might miss.” — PharmD Alex T., May 9, 2025
  - “Answers are accurate and the sources are easy to verify.” — Nurse Priya S., May 8, 2025
- Lookup Time Reduction (7-Day Trend):
  - Average summary time: **2m 18s**;
  - **↓ 24%**;
  - vs prior 7 days: **3m 02s**;
- Query Volume (7-Day Trend):
  - Authorized queries: **48**;
  - **↑ 14%**;
  - vs prior 7 days: **42**.

Some dashboard content is covered by the command palette and cannot be reliably transcribed.

## 12.9 UX behavior inferred

- The overlay supports both search and command execution.
- Results are grouped by entity type for fast scanning.
- Keyboard hints appear at row level and in the footer.
- Recent context minimizes typing for common clinician workflows.
- All global navigation is accessible without leaving the current page state.

---

# 13. Screen 7 — Request Patient Access

## 13.1 Screen purpose

Structured, auditable workflow for requesting access to a protected patient record after permission is denied.

## 13.2 Background access-denied page

Active sidebar item:

- Patients

Main state:

- **Access denied**
- **“You don’t have permission to view this patient’s record.”**
- supporting text indicates access is based on role, treatment relationship, and organizational policies.

“What you can do” panel:

1. **Request access**  
   Submit a request and a clinician with appropriate permissions will review it.

2. **Ask a question**  
   Get general information without accessing patient data.

3. **Return to dashboard**  
   Go back to your overview.

Bottom links:

- **Contact the Health Information Management team**
- **Patient access and data use policy**

Sidebar Recent Patients:

- John Carter — MRN 104582
- Maria Gonzalez — MRN 103991
- Robert Johnson — MRN 104113
- Aisha Patel — MRN 104905
- Emily Davis — MRN 105002

## 13.3 Modal header

Title:

- **Request patient access**

Subtitle:

- **Fill out the details below to request access to this patient’s record.**

Close icon at top-right.

## 13.4 Patient summary

- initials: JC
- **John Carter**
- **MRN 104582**
- DOB: **May 14, 1962 (63 y/o)**
- Admitted: **May 8, 2025**
- Status: **Inpatient** with blue dot.

## 13.5 Request fields

### Requested resource

- **Full patient record**
- helper: **Clinical data, notes, labs, imaging, and documents**

### Requested duration

- **7 days**
- **May 10 – May 17, 2025**

### Urgency level

- **Medium**
- **Within 24–72 hours**
- orange status dot.

### Your relationship to patient

- **Consulting physician**
- **Not primary care provider**

## 13.6 Purpose of access

Three selectable radio cards:

1. **For immediate treatment** — selected  
   Direct clinical care for this patient

2. **For care coordination**  
   Coordinate care with the care team

3. **For records review**  
   Review records for clinical or admin purposes

## 13.7 Clinical justification

Entered text:

> Patient is being evaluated for potential cardiac intervention. Need access to recent labs, imaging, and medication history to inform treatment plan and avoid contraindications.

Character count:

- **178/500**

## 13.8 Confirmation

Checked checkbox:

- **I confirm that this request is necessary for the stated purpose and will be logged in audit trails.**

Info icon follows the copy.

## 13.9 “How access requests work” rail

### Typical review time

- **Within 2–4 business hours during business days**

### Reviewed by

- **A clinician with appropriate permissions for this patient**

### You’ll be notified

- **When a decision is made, you’ll receive an update in Audit Logs and via email**

### Access is audit-logged

- **All requests and approvals are logged and monitored for compliance**

Urgent-access note:

- **Need urgent access?**
- **Contact the on-call HIM team or use the emergency override process if available.**

## 13.10 Footer actions

- **Cancel**
- primary: **Submit request** with lock icon.

## 13.11 UX behavior inferred

- The form asks for minimum necessary access scope, duration, urgency, relationship, purpose, and justification.
- Users must explicitly acknowledge audit logging.
- The right rail sets expectations before submission.
- An emergency path is named but kept separate from the standard workflow.
- The access request is framed as a compliance action, not merely a generic permission error.

---

# 14. End-to-end workflows represented

## 14.1 Permission-aware clinical answer

1. Select or open a patient.
2. Ask a clinical question.
3. Retrieve only authorized evidence.
4. If direct evidence exists, answer with citations.
5. If evidence is absent or insufficient, produce a safe refusal.
6. Explain why the answer cannot be supported.
7. Offer document search, upload, access request, or narrower query.

## 14.2 Document ingestion and indexing

1. Upload one or more documents.
2. Securely transfer to storage.
3. Run OCR parsing.
4. Split content into chunks.
5. Generate embeddings.
6. Store and index.
7. Surface document in semantic retrieval.

## 14.3 Low-confidence OCR exception

1. OCR confidence falls below threshold.
2. Mark document as Needs Review/OCR Failed.
3. Block text extraction/indexing completion.
4. Show source scan beside extracted text.
5. Highlight uncertain words.
6. Require checklist completion.
7. Approve and index or archive.

## 14.4 Citation verification

1. Open a source attached to an answer.
2. View original document page.
3. Inspect the exact extracted chunk.
4. Confirm source integrity.
5. Confirm authorization.
6. See PHI sensitivity.
7. Open the record in its source system if needed.

## 14.5 Access request

1. Attempt to open protected patient record.
2. Show access-denied state.
3. Open request modal.
4. Define requested resource and duration.
5. Set urgency and treatment relationship.
6. Select purpose.
7. Enter clinical justification.
8. Confirm audit logging.
9. Submit for authorized review.
10. Receive decision via Audit Logs and email.

---

# 15. Data and content model inferred from the UI

## 15.1 User

- name;
- avatar;
- specialty;
- role/permissions;
- last login;
- environment;
- audit status.

## 15.2 Patient

- name;
- MRN;
- initials/avatar;
- DOB;
- age;
- sex;
- specialty/service line;
- admission date;
- inpatient/outpatient status;
- clinician relationship;
- authorization state.

## 15.3 Document

- filename;
- document type;
- patient;
- source/source system;
- upload date;
- capture date;
- size;
- page count;
- OCR confidence;
- processing state;
- index state;
- page/chunk metadata;
- data sensitivity;
- source integrity;
- access authorization;
- audit history.

## 15.4 Conversation

- patient context;
- thread title;
- privacy state;
- created/updated timestamp;
- user messages;
- assistant messages;
- confidence;
- citations;
- feedback;
- bookmarks;
- streaming state.

## 15.5 Access request

- patient;
- requested resource;
- requested duration;
- urgency;
- requester relationship;
- purpose;
- clinical justification;
- acknowledgement;
- reviewer;
- status;
- audit events;
- notification channel.

---

# 16. Interaction and state specification

## 16.1 Loading

Expected treatments based on current visual language:

- inline spinner for active OCR/retry actions;
- determinate progress bars where percentage is known;
- stage stepper for batch progression;
- skeleton rows for semantic retrieval or document tables;
- disabled primary actions while critical operations run.

## 16.2 Success

- green outlined icon;
- green text/badge;
- explicit success label;
- completion timestamp where relevant.

## 16.3 Warning

- amber/orange badge and icon;
- explanation text;
- action to review, retry, or learn more;
- no silent degradation.

## 16.4 Error

- red label and red icon;
- reason shown in plain language;
- next action visible;
- operational details separated from user-facing explanation.

## 16.5 Empty or insufficient evidence

- illustrative empty-state graphic;
- concise title;
- explanation of scope/permissions;
- actionable recovery options;
- related-but-insufficient results retained for transparency.

## 16.6 Permission denied

- explicit access-denied message;
- no patient content leakage;
- alternatives: request access, ask a general question, return to dashboard;
- compliance-focused explanation.

## 16.7 Modal keyboard behavior recommended

- focus trapped inside modal;
- Escape closes only when safe;
- first meaningful field receives focus;
- Enter activates highlighted command in command palette;
- arrow keys navigate command results;
- destructive actions require confirmation if irreversible.

---

# 17. Accessibility assessment and recommendations

## 17.1 Strengths visible

- labels accompany semantic colors;
- large click targets;
- strong title hierarchy;
- selected states use both color and shape;
- info icons provide policy context;
- error and warning states include text explanations;
- keyboard shortcuts are exposed;
- modal backdrops produce clear visual focus.

## 17.2 Items to validate in implementation

1. Ensure all body text and light-gray helper text meet WCAG AA contrast.
2. Do not rely only on green/red/orange for statuses; preserve visible labels and icons.
3. Add accessible names to icon-only controls such as filter, bookmark, overflow, rotate, fullscreen, and close.
4. Announce upload progress and OCR-state changes through polite live regions.
5. Make table headers programmatically associated with data cells.
6. Ensure extracted-text uncertainty highlights have non-color indicators for screen readers.
7. Give the relevance-dot scale an explicit text value.
8. Provide keyboard operation for page thumbnails and document zoom controls.
9. Announce why **Approve & Index** is unavailable if checklist requirements are unmet.
10. Preserve focus when opening and closing nested viewers or source-system links.

---

# 18. Content design and clinical-safety observations

## 18.1 Strong content patterns

- Refusal language is direct, non-accusatory, and explains the evidence boundary.
- The system avoids a vague “no results” message and differentiates related-but-insufficient material.
- Access requests explain who reviews them and when.
- Audit logging is repeatedly reinforced without dominating the screen.
- Clinical copy uses full terms and avoids unexplained abbreviations in interaction text.
- Suggested next steps are phrased as concrete actions.

## 18.2 Consistency recommendations

- Standardize punctuation and capitalization in button labels. **“Safe. Refusal Test”** appears unusual and may be a prototype-only control.
- Use one canonical naming format for filenames and visible display titles. Some names use underscores while sidebar labels use sentence case.
- Standardize status vocabulary across the dashboard and modal. For example, a document is shown as **OCR Processing** in one context and **Needs review / OCR confidence low** in another; this may be temporal, but the state machine should be explicit.
- Clarify whether a confidence percentage is OCR confidence, retrieval relevance, or answer confidence by always labeling the metric.
- Consider exposing a “why this result” affordance on semantic-search matches.

---

# 19. Data-quality issues visible in the synthetic content

These are content QA observations, not interface-design failures.

1. **John Carter age mismatch:** DOB is May 14, 1962, while the May 10, 2025 access-request screen labels him 63 y/o. He would still be 62 until May 14, 2025.
2. **Maria Gonzalez age mismatch:** the referral dated May 8, 2025 lists DOB 07/14/1975 but describes a 58-year-old female. The DOB corresponds to age 49 at that date.
3. **Atorvastatin dose differs across records:** the referral scan shows 20 mg nightly, while the medication-list/discharge semantic results show 40 mg nightly. This may reflect a legitimate medication change, but the UI should make effective dates and reconciliation status easy to compare.
4. **Potential status mismatch:** the cardiology consult appears as **OCR Processing** in the document table and **Needs review / OCR confidence low** in the upload modal. If these are concurrent snapshots, status-transition timing should be clarified.

For a clinical product, synthetic fixtures should be internally consistent unless discrepancies are intentionally included for reconciliation testing.

---

# 20. Professional UX assessment

## 20.1 What works especially well

- **Trust architecture is embedded in the workflow.** Authorization, evidence, source integrity, and auditability are not relegated to settings pages.
- **The refusal state is exemplary.** It avoids hallucination while still helping the user move forward.
- **Document operations are understandable.** The pipeline maps technical stages to human-readable labels.
- **The citation viewer is clinically credible.** It supports verification at the original-document level.
- **High-risk actions are deliberate.** Indexing, archiving, and requesting access have clear visual differentiation.
- **The command palette is efficient.** It unifies entities and actions without replacing standard navigation.
- **The visual hierarchy is calm.** Dense operational information remains readable because grouping and whitespace are strong.

## 20.2 Improvement opportunities

- Make the editability of extracted OCR text visually explicit with a cursor, edit mode, or inline instruction.
- Add a visible state-transition legend for document processing.
- Provide an access-request status tracker after submission.
- Add direct comparison/reconciliation UI when medication values differ across documents.
- Consider sticky headers in long document tables and long extracted-text panels.
- Expose filters for date, source, and body region directly in evidence retrieval.
- Confirm that all modal layouts remain usable at laptop heights below 900 px.
- Add clear confirmation for destructive archive actions.
- Consider showing source freshness and last-sync information in semantic-search results.

---

# 21. Responsive behavior recommendations

The supplied designs are desktop-only. Recommended adaptations:

## ≥ 1280 px

- preserve sidebar, main canvas, and right rail;
- use full tables and document side-by-side review.

## 1024–1279 px

- collapse right evidence rail into a drawer;
- reduce sidebar width or convert it to icon-plus-tooltip mode;
- keep tables horizontally scrollable if required.

## 768–1023 px

- use temporary navigation drawer;
- stack semantic search below document table;
- turn citation details into a secondary tab;
- stack scan and extracted text with a compare toggle.

## < 768 px

- prioritize patient identity, safety state, and key actions;
- replace wide tables with card lists;
- use full-screen modals/sheets;
- show one document page at a time;
- preserve access-request fields in a single vertical column.

---

# 22. Suggested component naming for implementation

```text
AppShell
TopBar
BrandLockup
GlobalSearchTrigger
EnvironmentSelector
UserProfileMenu
PrimarySidebar
SidebarNavItem
RecentEntityList
PermissionScopeCard
AuditStatusBadge

PageHeader
SectionCard
MetricCard
StatusBadge
InfoTooltip
EmptyState
AlertBanner
ActionButton
IconButton
OverflowMenu

PatientContextChip
AuthorizationBadge
ThreadHeader
MessageBubble
AssistantSafetyCard
ConfidenceBadge
SuggestedActionCard
ClinicalComposer
EvidenceRail
EvidenceResultCard

DocumentDropzone
DocumentFilterBar
DocumentTable
DocumentStatusCell
OCRConfidenceCell
Pagination
SemanticSearchPanel
SemanticResultCard
ProcessingStepper
StorageUsageChart

UploadBatchModal
UploadFileRow
FileProgressBar
SecurityComplianceStrip

DocumentReviewWorkspace
PageThumbnailRail
DocumentViewer
ViewerToolbar
ExtractedTextPanel
UncertainTokenHighlight
ProcessingTimeline
FailureReasonList
ReviewChecklist

CitationViewerModal
CitationDetailsPanel
ExtractedSnippetCard
RelevanceScale
VerificationList

CommandPalette
CommandGroup
CommandResultRow
KeyboardShortcutBadge

AccessDeniedState
AccessRequestModal
PatientSummaryStrip
AccessScopeSelect
PurposeRadioCard
ClinicalJustificationField
AuditAcknowledgement
AccessRequestExplainer
```

---

# 23. Acceptance criteria for a faithful rebuild

A high-fidelity implementation should satisfy the following:

1. The desktop shell reproduces the fixed top bar, left sidebar, main canvas, and optional right rail.
2. Active navigation is represented with a pale blue rounded surface and blue icon/text.
3. Cards use subtle borders, white fill, and restrained radius rather than heavy shadows.
4. Primary actions use a saturated clinical blue and high-contrast white text.
5. Success, warning, error, purple safety, and neutral states each have consistent badge semantics.
6. The safe-refusal page reproduces all explanatory copy, related-but-insufficient evidence, confidence state, and remediation actions.
7. The documents dashboard includes the complete ten-row table, filters, semantic-search cards, pipeline metrics, and storage chart.
8. The OCR review screen presents thumbnails, scan, extracted text, low-confidence highlights, timeline, failure reasons, and checklist simultaneously at the reference width.
9. The upload modal supports mixed per-file progress states.
10. The citation viewer exposes original content, page/chunk metadata, access data, verification, and PHI sensitivity.
11. The command palette supports keyboard navigation and grouped recent entities/commands.
12. The access-request modal records scope, duration, urgency, relationship, purpose, justification, and audit acknowledgement.
13. All icon-only controls have accessible labels.
14. All critical state changes are available to assistive technology.
15. Permission-denied states never expose protected patient content beyond the approved summary identity required to request access.

---

# 24. Final design characterization

This UI set represents a mature enterprise healthcare assistant rather than a generic chatbot. Its strongest quality is the integration of **clinical evidence, authorization, provenance, OCR quality control, and auditability directly into routine workflows**. The product uses familiar SaaS interaction patterns—side navigation, cards, tables, command palette, drawers/modals—but adapts them to healthcare risk through explicit confidence labels, safe refusal, source verification, and access governance.

The visual tone is professional and calm: deep navy for trust, blue for action, green for verification, purple for AI safety, amber for uncertainty, and red for failures or destructive actions. Layouts are information-dense but remain approachable through strong grouping, generous whitespace, and concise microcopy.

For implementation, the most important invariant is not merely pixel fidelity. It is preserving the system’s hierarchy of trust:

1. patient and authorization context;
2. evidence availability;
3. answer confidence;
4. source provenance;
5. human review when automation is uncertain;
6. full auditability of sensitive actions.

