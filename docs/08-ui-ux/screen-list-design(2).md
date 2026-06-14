# screen-list-design.md — AI-Powered Hospital Knowledge Assistant

Tài liệu mô tả danh sách màn hình theo các PNG đã cung cấp. Mỗi màn hình có: tên route/state, mục tiêu, bố cục ASCII, component chính, nội dung hiển thị nổi bật và hành vi tương tác. Cuối file có thêm **5 màn hình đề xuất bổ sung** theo cùng design system.

---

## 0. Global shell pattern

```ascii
+------------------------------------------------------------------------------------------------+
| [Shield+Cross Logo] AI-Powered Hospital Knowledge Assistant | Search.............[⌘K] | Data | User |
+------------------------+-----------------------------------------------------------------------+
| Sidebar                | Main content                                              | Right rail |
|                        |                                                           | optional   |
| Nav items              | Page title / context chips / toolbar                      |            |
| Recent items           | Cards / table / chat / docs / metrics                     |            |
| Permission-aware card  | Footer disclaimer: AI can make mistakes. Verify... Learn  |            |
| Audit ready footer     |                                                           |            |
+------------------------+-----------------------------------------------------------+------------+
```

**Global UI constants visible across PNG:**

- Product label: `AI-Powered Hospital Knowledge Assistant`.
- Data pill: `Synthetic Data` with database icon.
- Logged-in user: `Dr. Sarah Chen`, specialty `Cardiology`.
- Safety footer: `AI can make mistakes. Verify important information. Learn more`.
- Sidebar footer: `Audit ready` + `Last login: May 10, 2025, 8:51 AM`.
- Left nav: Dashboard, Patients, Chat, Documents, Timeline, Audit, Metrics, Settings.

---

# A. Access control & access request

---

## 1. access-control.denied.no-treatment-relationship

**PNG:** `access-control.denied.no-treatment-relationship.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Patients / Access denied / No active treatment relationship`  
**Purpose:** chặn truy cập hồ sơ bệnh nhân khi bác sĩ không có quan hệ điều trị đang hoạt động; hiển thị lý do, audit status và next actions.

```ascii
+------------------------------------------------------------------------------------------------+
| Logo/Product | Global search....................................[⌘K] | Synthetic Data | User   |
+----------------------+-----------------------------------------------------------------------------+
| Sidebar              | +-----------------------------------------------------------+ +---------------+ |
| # Patients           | |                    [large shield + lock]                  | | What you can  | |
| Recent Patients      | |                                                           | | do next       | |
|  John Carter         | |                    Access denied                         | | - Request     | |
|  Maria Gonzalez      | | You do not currently have permission...                  | | - Check rel.  | |
|  Robert Johnson      | | All sensitive access attempts are logged...              | | - Review pol. | |
|  Aisha Patel         | |-----------------------------------------------------------| | - Contact sup.| |
|  Emily Davis         | | Request details                                           | +---------------+ |
| Permission card      | | +-----------------------+ +-----------------------------+ | +---------------+ |
|                      | | | Requested patient     | | Requested resource          | | Why blocked   | |
|                      | | | Jane Smith MRN 507831 | | Patient Summary             | | Privacy       | |
|                      | | +-----------------------+ +-----------------------------+ | | Role-based    | |
|                      | | +-----------------------+ +-----------------------------+ | | Compliance    | |
|                      | | | Reason                | | Audit status                | | View policy ↗ | |
|                      | | | No active treatment   | | Logged                      | +---------------+ |
|                      | | +-----------------------+ +-----------------------------+ |                 |
|                      | | [Back to Patients] [Request Access] [View Access Policy]   |                 |
|                      | | [Need immediate access? Contact Support]                   |                 |
+----------------------+ +-----------------------------------------------------------+-----------------+
```

**Visual details:**

- Central card lớn nền trắng, border xanh xám, nhiều khoảng trắng.
- Hero icon shield-lock xanh ở giữa, xung quanh có icon phụ dạng dotted orbit.
- Title `Access denied` rất lớn, text navy đậm.
- Request details là 2×2 grid; mỗi cell có icon tròn pastel và label nhỏ.
- Lý do chính: `No active treatment relationship`.
- Audit status: `Logged`, icon check xanh.
- CTA chính màu xanh: `Back to Patients`; CTA phụ outline: `Request Access`, `View Access Policy`.
- Right rail chia 2 card: `What you can do next` và `Why this was blocked`.

**Components:** `AccessDeniedPanel`, `RequestDetailsGrid`, `NextActionsRail`, `PolicyReasonCard`, `PermissionAwareSidebarCard`.

---

## 2. access-requests.create.clinical-justification-modal

**PNG:** `access-requests.create.clinical-justification-modal.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Access Request / Create / Modal`  
**Purpose:** cho phép bác sĩ gửi yêu cầu truy cập bệnh nhân, kèm resource, duration, urgency, relationship, purpose và justification.

```ascii
+------------------------------------------------------------------------------------------------+
| Dimmed app shell: Patients page + access denied content in background                            |
|                                                                                                |
|                 +---------------------------------------------------------------+              |
|                 | Request patient access                                  [X]  |              |
|                 | Fill out the details below...                                |              |
|                 | +---------------------------------------------------------+ |              |
|                 | | [JC] John Carter | MRN 104582 | DOB | Admitted | Status | |              |
|                 | +---------------------------------------------------------+ |              |
|                 | +------------------------------+ +------------------------+ | +----------+ |
|                 | | Requested resource        v  | | Requested duration   v | | How      | |
|                 | | Full patient record          | | 7 days                 | | requests | |
|                 | +------------------------------+ +------------------------+ | | work     | |
|                 | +------------------------------+ +------------------------+ | | Typical  | |
|                 | | Urgency level             v  | | Relationship          v | | review   | |
|                 | | Medium                       | | Consulting physician    | | Reviewed | |
|                 | +------------------------------+ +------------------------+ | | Notify   | |
|                 | Purpose of access                                             | | Audit    | |
|                 | +-------------+ +-------------+ +-------------+             | | logged   | |
|                 | | ● Immediate | | Care coord | | Records rev |             | +----------+ |
|                 | +-------------+ +-------------+ +-------------+             |              |
|                 | Clinical justification                                        |              |
|                 | +---------------------------------------------------------+ |              |
|                 | | Patient is being evaluated for potential cardiac...      | |              |
|                 | | ...avoid contraindications.                         178/500|              |
|                 | +---------------------------------------------------------+ |              |
|                 | [✓] I confirm this request is necessary... audit trails.     |              |
|                 |                                      [Cancel] [Submit request] |              |
|                 +---------------------------------------------------------------+              |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Overlay tối phủ toàn app; modal trắng ở giữa, radius lớn.
- Modal content chia 2 cột: form chính bên trái rộng, explainer rail bên phải.
- Header patient compact card gồm avatar initials `JC`, tên `John Carter`, MRN, DOB, admitted date, status `Inpatient`.
- Radio-card purpose: `For immediate treatment` đang được chọn, border xanh.
- Textarea justification có counter `178/500`.
- Checkbox confirmation đã checked; submit button có icon lock.
- Side explainer là vertical timeline với icon: shield, clock, user, bell, lock.

**Components:** `AccessRequestModal`, `PatientSummaryStrip`, `SelectField`, `PurposeRadioCard`, `ClinicalJustificationTextarea`, `AuditConfirmationCheckbox`, `ExplainerTimeline`.

---

# B. Audit & compliance

---

## 3. audit.logs.access-event-detail-panel

**PNG:** `audit.logs.access-event-detail-panel.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Audit Logs / Event selected / Detail drawer`  
**Purpose:** xem audit trail cho sensitive data access và system actions; hỗ trợ filter, export, detail panel.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+--------------------------------------------------------------------------+
| Sidebar             | Audit Logs                                         [Export] [...] | Drawer |
| # Audit             | Complete traceability...                                      | Details |
| Recent Threads      | +-----------+ +-----------+ +-----------+ +-----------+       | [X]     |
| Permission card     | | Events    | | Denied    | | Queries   | | Missing   |       | Allowed |
|                     | | 1,248 ↑   | | 23 ↑      | | 986 ↑     | | 0         |       | EventID |
|                     | +-----------+ +-----------+ +-----------+ +-----------+       | Tabs    |
|                     | +----------------------------------------------------------------+ |      |
|                     | | User v | Patient v | Action v | Date range | Result v |Filter| |      |
|                     | +----------------------------------------------------------------+ |      |
|                     | 1,248 events   Updated 2 min ago                                  | User   |
|                     | +----------------------------------------------------------------+ | Role   |
|                     | | Timestamp | User | Role | Patient | Action | Resource | Result | > | Patient|
|                     | |● 9:18 AM | Sarah|Phys | John    | View note | Note | Allowed |   | Action |
|                     | |●/● rows alternating allowed/denied events...                   | | Result |
|                     | +----------------------------------------------------------------+ | Context|
|                     | Pagination: 1-25 of 1,248  < 1 2 3 ... 50                       | PHI    |
|                     | +-----------------------+ +-------------------------------+       | MFA    |
|                     | | Permission-aware     | | 100% sensitive query logging |       | Desc   |
|                     | +-----------------------+ +-------------------------------+       |        |
+---------------------+--------------------------------------------------------------------------+
```

**Visual details:**

- Page title có shield icon outline.
- 4 KPI cards đầu trang: `Total Events Today 1,248`, `Denied Access Attempts 23`, `Patient Queries Logged 986`, `Missing Audit Events 0`.
- Denied card dùng đỏ; query card dùng tím; missing audit dùng xanh.
- Filter bar ngay trên table, có badge `Filters 2`.
- Row đầu được selected: border xanh, dot xanh, result chip `Allowed`.
- Drawer phải rộng ~300 px, có title `Audit Event Details`, close icon, status chip `Allowed`, event id.
- Drawer có tabs `Overview`, `Raw Event`; Overview active bằng underline xanh.
- Context section có `Application`, `Client IP`, `Device`, `Location`, `Session ID`, `Data Sensitivity PHI - High`, `MFA Verified`.

**Components:** `AuditMetricCard`, `AuditFilterBar`, `AuditEventsTable`, `AuditEventDrawer`, `ComplianceInfoCard`.

---

# C. Authentication

---

## 4. auth.login.staff-sso-email-password

**PNG:** `auth.login.staff-sso-email-password.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Auth / Login / SSO + Email`  
**Purpose:** trang đăng nhập staff bằng Hospital SSO hoặc email/password, nhấn mạnh bảo mật và HIPAA.

```ascii
+--------------------------------------------------+--------------------------------------------------+
| [Logo] AI-Powered Hospital Knowledge Assistant   |                         [Synthetic Data v]       |
|                                                  |                                                  |
| Smarter insights.                                |       +----------------------------------+       |
| Better patient care.                             |       | Welcome back                     |       |
|                                                  |       | Sign in to your...                |       |
| Securely ingest, search, and analyze...          |       | [ Sign in with Hospital SSO ]     |       |
|                                                  |       | ------- or continue with email ---|       |
| [shield] Enterprise-Grade Security               |       | Email address                     |       |
| [lock] Privacy by Design                         |       | [ mail  Enter your email       ]  |       |
| [search] Trusted & Transparent                   |       | Password                          |       |
| [chart] Built for Healthcare                     |       | [ lock  Enter password     eye ]  |       |
|                                                  |       | [✓] Remember this device  Forgot? |       |
|       soft 3D medical document + shield art      |       | [ Sign in with email disabled ]   |       |
|                                                  |       | + Secure access. Your data...   + |       |
| Trusted by healthcare organizations...           |       | PHI Protection | Audit | Role     |       |
|                                                  |       +----------------------------------+       |
|                                                  |       Need help? Contact your IT administrator    |
|                                                  |       © 2025 ...                                |
+--------------------------------------------------+--------------------------------------------------+
```

**Visual details:**

- Split 45/55: left marketing pane gradient xanh cực nhạt; right login card.
- Logo top-left lớn hơn app shell, không có sidebar.
- H1 marketing `Smarter insights. Better patient care.` kích thước lớn.
- 4 feature bullets có icon pastel: security, privacy, transparent, healthcare.
- Login card shadow nhẹ, radius lớn, centered.
- CTA SSO màu xanh full-width với shield icon.
- Divider có text `or continue with email`.
- Email/password inputs có icon; password có eye icon.
- Email button disabled vì chưa nhập form.
- Trust card trong login card có shield green icon và 3 chips: PHI Protection, Audit Logging, Role-Based Access.

**Components:** `AuthSplitLayout`, `MarketingFeatureList`, `LoginCard`, `SSOButton`, `EmailPasswordForm`, `SecurityAssuranceBox`.

---

## 5. auth.mfa.verify-identity-code

**PNG:** `auth.mfa.verify-identity-code.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Auth / MFA / Verify identity`  
**Purpose:** xác thực MFA bằng mã 6 chữ số, có countdown và lựa chọn phương thức khác.

```ascii
+------------------------------------------------------------------------------------------------+
|                                      [Logo] AI-Powered Hospital                                |
|                                      Knowledge Assistant                                       |
|                                                                                                |
|                    +------------------------------------------------------+                    |
|                    |                 [lock icon tile]                    |                    |
|                    |              Verify your identity                   |                    |
|                    |       For your security, we need to verify...       |                    |
|                    | [mail] We sent a 6-digit code to s***@city...       |                    |
|                    | Enter 6-digit code                                  |                    |
|                    | [ | ] [ – ] [ – ] [ – ] [ – ] [ – ]                |                    |
|                    | [clock] Code expires in 01:45 | [refresh] Resend   |                    |
|                    | ------------------ or ----------------------------- |                    |
|                    | [shield] Use another method                    v    |                    |
|                    | [ Verify & Continue                         → ]     |                    |
|                    +------------------------------------------------------+                    |
|                                                                                                |
|          +--------------------------------------------------------------------------+          |
|          | [shield] Your data is protected | [check] MFA ... | [doc] Audit-ready    |          |
|          +--------------------------------------------------------------------------+          |
|                         Need help? Contact IT Support ↗ | Return to sign in                    |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Auth page centered card, không split; background trắng/xanh nhạt với watermark shield trái và lock phải.
- Logo centered top.
- MFA card trắng, shadow/radius lớn.
- 6 input ô vuông; ô đầu focus border xanh.
- Countdown màu xanh cho `01:45`; resend là link xanh.
- CTA primary full-width, text `Verify & Continue`, arrow phải.
- Dưới có horizontal trust strip 3 phần, chia bằng divider.

**Components:** `MFACard`, `OtpInputGroup`, `CountdownResend`, `MethodSelect`, `AuthTrustStrip`.

---

# D. Dashboard

---

## 6. dashboard.empty.workspace-onboarding-first-data

**PNG:** `dashboard.empty.workspace-onboarding-first-data.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Dashboard / Empty workspace`  
**Purpose:** onboarding workspace chưa có patient/document/thread/activity.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+-----------------------+------------------------------------------------------------------------+
| Sidebar               | Welcome back, Dr. Sarah Chen 👋                    [Customize dashboard] |
| # Dashboard           | Access trusted knowledge...                                             |
| Recent Threads empty  | +--------------------------------------------------------------+ +------+ |
| Permission card       | |                         illustration                         | |Recent| |
|                       | |                         No data yet                          | |Thread| |
|                       | | Get started by adding your first patient or uploading...     | |empty | |
|                       | | [Upload first document] [Add first patient]                   | +------+ |
|                       | +--------------------------------------------------------------+ +------+ |
|                       | +----------+ +----------+ +----------+ +----------+            |Activity|
|                       | |Patients  | |Documents | |Queries   | |Citations |            |Feed   |
|                       | |skeleton | |skeleton  | |skeleton  | |skeleton  |            |empty  |
|                       | +----------+ +----------+ +----------+ +----------+            +------+ |
+-----------------------+------------------------------------------------------------------------+
```

**Visual details:**

- Empty hero card chiếm phần lớn top-left, có illustration folder + clipboard 3D mềm.
- Title `No data yet`, subcopy hướng dẫn thêm bệnh nhân hoặc upload document.
- CTA primary xanh `Upload first document`, CTA secondary `Add first patient`.
- KPI cards phía dưới ở skeleton/placeholder trạng thái chưa có dữ liệu.
- Right column: `Recent Threads` empty card + `Activity Feed` empty card.

**Components:** `DashboardEmptyHero`, `SkeletonMetricCard`, `EmptyRecentThreadsCard`, `EmptyActivityFeedCard`.

---

## 7. dashboard.overview.action-success-toast

**PNG:** `dashboard.overview.action-success-toast.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Dashboard / Populated / User menu opened`  
**Purpose:** dashboard có dữ liệu, trạng thái user menu mở ở góc phải. Tên file có “toast”, nhưng trong PNG nhìn thấy rõ dropdown user menu; không thấy toast success riêng biệt.

```ascii
+------------------------------------------------------------------------------------------------+
| Logo | Search................................[⌘K] | Synthetic Data | Shield | [User ▼ OPEN]      |
+----------------------+-------------------------------------------------------+------------------+
| Sidebar              | Good morning, Dr. Sarah Chen 👋                                        | User menu        |
| # Dashboard          | Accelerate care with trusted...                                        | +--------------+ |
| Recent Threads       | +-------------+ +-------------+ +-------------+ +-------------+      | | avatar/name  | |
| Permission card      | | Avg Summary| | Cited Ans. | | Auth Query | | Indexed Docs|      | | Physician    | |
|                      | | 2m18s ↓24% | | 94.6% ↑   | | 48 ↑14%   | | 12,842 ↑  |      | +--------------+ |
|                      | +-------------+ +-------------+ +-------------+ +-------------+      | My Profile      |
|                      | +---------------------------------------+ +--------------------+      | Preferences     |
|                      | | Find patient or start new task        | | Recent Threads    |      | Switch Role >   |
|                      | | [Search by name, MRN...]              | | thread list       |      | Switch Workspace|
|                      | | [Ask] [Generate] [Upload]             | +--------------------+      | Help & Support  |
|                      | +---------------------------------------+ +--------------------+      | Log out red     |
|                      | +---------------------------------------+ | Document Status   |      +-----------------+
|                      | | Recent Patients table                 | +--------------------+                        |
|                      | +---------------------------------------+ | Safety & Access    |                        |
+----------------------+-------------------------------------------------------+------------------+
```

**Visual details:**

- Dashboard populated có 4 KPI cards ngang.
- User dropdown floating dưới avatar, shadow rõ, radius 12–16.
- Dropdown header: avatar lớn, `Dr. Sarah Chen`, `Cardiology`, chip `Physician`.
- Menu item có icon trái: `My Profile`, `Preferences`, `Switch Role`, `Switch Workspace`, `Help & Support`, `Log out` đỏ.
- Recent Patients table có avatar patient, age/sex, MRN, department, last activity, action icons.
- Safety & Access card có 3 dòng: Permission-aware retrieval Active, Audit logging Enabled, Safe refusal Active.

**Components:** `DashboardOverview`, `UserProfileDropdown`, `MetricCard`, `QuickTaskPanel`, `RecentPatientsTable`, `SafetyAccessCard`.

---

## 8. dashboard.overview.populated-hms-ai-workspace

**PNG:** `dashboard.overview.populated-hms-ai-workspace.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Dashboard / Populated / Charts visible`  
**Purpose:** dashboard operational đầy đủ, bổ sung trend charts ở cuối trang.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+--------------------------------------------------------------------------+
| Sidebar             | Good morning, Dr. Sarah Chen 👋                 [Customize dashboard]     |
| # Dashboard         | +---------+ +---------+ +---------+ +---------+                         |
| Recent Threads      | | 2m18s   | | 94.6%  | | 48     | | 12,842 |                         |
| Permission card     | +---------+ +---------+ +---------+ +---------+                         |
|                     | +--------------------------------+ +-------------------------------+     |
|                     | | Find a patient/start task      | | Recent Threads                 |     |
|                     | +--------------------------------+ +-------------------------------+     |
|                     | +--------------------------------+ +-------------------------------+     |
|                     | | Recent Patients table          | | Document Processing Status     |     |
|                     | | 5 patients listed              | +-------------------------------+     |
|                     | +--------------------------------+ | Safety & Access                |     |
|                     |                                  +-------------------------------+     |
|                     | +--------------------------------+ +-------------------------------+     |
|                     | | Lookup Time Reduction chart    | | Query Volume 7-day chart       |     |
|                     | +--------------------------------+ +-------------------------------+     |
+---------------------+--------------------------------------------------------------------------+
```

**Visual details:**

- Tương tự screen 7 nhưng profile dropdown đóng và có thêm chart row cuối.
- Chart 1: line chart `Lookup Time Reduction (7-Day Trend)`, average summary time `2m 18s`, trend `↓ 24%`.
- Chart 2: bar chart `Query Volume (7-Day Trend)`, authorized queries `48`, trend `↑ 14%`.
- Document Processing Status dùng icon tròn lớn: uploaded, indexing, indexed, failed.

**Components:** `TrendLineChartCard`, `QueryVolumeBarChartCard`, `ProcessingStatusSummary`.

---

# E. Patients

---

## 9. patients.empty.no-results-or-no-access

**PNG:** `patients.empty.no-results-or-no-access.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Patients / Empty or no authorized access`  
**Purpose:** hiển thị danh sách bệnh nhân rỗng; có CTA add/import và quick actions.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+----------------------+---------------------------------------------------------+--------------+
| Sidebar              | Patients                                  [Import] [Add Patient] | Saved Filters|
| # Patients           | Search, view, and manage patient records...                    | No saved     |
| Recent Patients      | +-------------------------------------------------------------+ | filters      |
|  No recent patients  | | Search by name, MRN, or phone... [⌘K] [All] [Dept] [Status]| +-------------+|
| Permission card      | +-------------------------------------------------------------+ | Patient      |
|                      | |                    illustration                            | | Alerts      |
|                      | |                    No patients found                       | | No alerts   |
|                      | | Get started by adding... or import existing records        | +-------------+|
|                      | | [Add First Patient] [Import Records]                       | | Quick       |
|                      | +-------------------------------------------------------------+ | Actions     |
|                      | +-------------------------------------------------------------+ | Upload list |
|                      | | Patient | MRN | Department | Last Activity | Status | Actions| | Merge       |
|                      | |                 No patients to display                     | | Audit Logs  |
|                      | +-------------------------------------------------------------+ +-------------+|
+----------------------+---------------------------------------------------------+--------------+
```

**Visual details:**

- Sidebar recent patients empty có text: patients you view will appear here.
- Main header có 2 CTA phải: `Import Records`, primary `Add Patient`.
- Filter/search row vẫn hiện trước empty hero để người dùng hiểu có thể lọc.
- Empty hero icon clipboard/search + people, title `No patients found`.
- Dưới empty hero vẫn giữ table header + empty row.
- Right rail gồm `Saved Filters`, `Patient Alerts`, `Quick Actions`.

**Components:** `PatientsEmptyState`, `PatientsFilterBar`, `EmptyTable`, `SavedFiltersCard`, `QuickActionsCard`.

---

## 10. patients.list.scoped-alerts-recent-activity

**PNG:** `patients.list.scoped-alerts-recent-activity.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Patients / Authorized scoped list`  
**Purpose:** danh sách patient trong phạm vi quyền truy cập của bác sĩ, có alerts và activity.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+----------------------------------------------------------+---------------+
| Sidebar             | Patients                                                  | Saved Filters |
| # Patients          | Search and manage patients within your authorized scope.  | My Inpatients |
| Recent Threads      | +---------+ +---------+ +---------+ +---------+          | High-Risk     |
| Permission card     | | Scope   | | Active  | | HighRisk| | Recent  |          | Today's       |
|                     | | 5,842 ↑ | | 142 ↑   | | 318 ↑   | | 67 ↑    |          | Follow-up     |
|                     | +---------+ +---------+ +---------+ +---------+          | Cardiology    |
|                     | +------------------------------------------------------+  +---------------+
|                     | | Search by patient name, MRN, DOB... [⌘K] [Filters 2] |  | Patient Alerts|
|                     | | Dept v | Status v | Physician v | Sort v | Clear all  |  | Sophia allergy|
|                     | +------------------------------------------------------+  | Robert CKD   |
|                     | Showing 1-8 of 8 patients                               |  | John highrisk|
|                     | +------------------------------------------------------+  +---------------+
|                     | | □ Patient | MRN | Age/Sex | Dept | Status | Physician |  | Recent       |
|                     | | □ John Carter    104582 63/M Cardio Inpatient Sarah |  | Activity     |
|                     | | □ Emily Davis    ...                                 |  | doc/lab/note |
|                     | | □ Maria Gonzalez ...                                 |  +---------------+
|                     | +------------------------------------------------------+                  |
|                     | Pagination < 1 >       rows/page 10        Go to page 1                 |
+---------------------+--------------------------------------------------------------------------+
```

**Visual details:**

- KPI cards: `Patients in Scope 5,842`, `Active Inpatients 142`, `High-Risk Patients 318`, `Recent Admissions 67`.
- High-Risk metric dùng cam; recent admissions dùng tím.
- Patient list có checkbox, avatar, name + MRN small, MRN col, age/sex, department icon, status chips, physician avatar, action icons.
- Right rail Saved Filters có item count pills; Patient Alerts có severity icons; Recent Activity có colored document/action icons.

**Components:** `ScopedPatientMetrics`, `PatientsDataTable`, `PatientAlertsCard`, `RecentActivityCard`, `SavedFiltersList`.

---

## 11. patients.ai-summary.stream-citations-retrieving

**PNG:** `patients.ai-summary.stream-citations-retrieving.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Chat / Patient summary / AI streaming with citations retrieving`  
**Purpose:** AI đang tạo summary cho patient Robert Johnson, evidence rail đang truy xuất và xác thực citation.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+----------------------------------------------------+---------------------+
| Sidebar             | [Patient: Robert Johnson MRN 104113] [Authorized]  | Evidence & Citations|
| # Chat              | Patient summary request                            | Retrieving...       |
| Recent Threads      | Today, 9:12 AM • private                           | ● Retrieving evid.  |
| Permission card     | +-----------------------------------------------+  | ○ Validating cit.   |
|                     | | User bubble: Provide comprehensive patient...  |  | ○ Streaming answer |
|                     | +-----------------------------------------------+  | +-----------------+ |
|                     | +-----------------------------------------------+  | | 1 Discharge ... | |
|                     | | AI Assistant [Generating...]                   |  | | 98%             | |
|                     | | Here is the latest clinical summary...         |  | | snippet         | |
|                     | | Patient Overview                               |  | +-----------------+ |
|                     | | • 72-year-old male with CKD...                 |  | +-----------------+ |
|                     | | Recent Clinical Status                         |  | | 2 Retrieving... | |
|                     | | Patient remains hemodynamically stable...      |  | | skeleton        | |
|                     | | skeleton lines + generating dots               |  | +-----------------+ |
|                     | | [thumb] [copy]  Confidence: High               |  | +-----------------+ |
|                     | +-----------------------------------------------+  | | 3 Retrieving... | |
|                     | Composer: Ask... [Stop] [Generate] [Safe Test]    | +-----------------+ |
+---------------------+----------------------------------------------------+---------------------+
```

**Visual details:**

- Main chat column rộng, right evidence rail cố định.
- Patient context chip trên cùng màu xanh/white, kèm `Authorized` chip.
- Assistant card đang stream: label `Generating...`, skeleton lines, dots.
- Confidence chip `High` ở footer card.
- Right rail stepper 3 bước; source card đầu đã retrieved, 2 card còn lại skeleton.
- Source card đầu: `Discharge_Summary_2025-05-10.pdf`, confidence `98%`, metadata page/chunk/captured/source/accessed.

**Components:** `PatientContextHeader`, `StreamingAnswerCard`, `EvidenceRetrievalStepper`, `CitationLoadingCard`, `ChatComposer`.

---

## 12. patients.medication-review.cited-safety-answer

**PNG:** `patients.medication-review.cited-safety-answer.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Chat / Medication and allergy review / Cited answer`  
**Purpose:** AI trả lời medication/allergy risks cho John Carter kèm citations đã xác thực.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+----------------------------------------------------+---------------------+
| Sidebar             | [Patient: John Carter MRN 104582] [Authorized]    | Evidence & Citations|
| # Chat              | Medication and allergy review                     | Permission-aware    |
| Recent Threads      | Today, 9:18 AM • private                          | +-----------------+ |
| Permission card     | +----------------------------------------------+   | | 1 Allergy Note  | |
|                     | | User: Summarize current allergies...          |   | | clinical note   | |
|                     | +----------------------------------------------+   | | snippet/relev.  | |
|                     | +----------------------------------------------+   | +-----------------+ |
|                     | | AI answer card                                |   | +-----------------+ |
|                     | | Allergies                                    |   | | 2 Medication    | |
|                     | | • Penicillin—rash [1]                        |   | | structured data | |
|                     | | • Iodinated contrast—hives [1]               |   | +-----------------+ |
|                     | | Active Medications                            |   | +-----------------+ |
|                     | | • Lisinopril 10 mg... [2]                    |   | | 3 Encounter     | |
|                     | | Potential Risk                                |   | | note            | |
|                     | | • Hyperkalemia risk... [3]                   |   | +-----------------+ |
|                     | | Recommendation                                |   | See all sources   |
|                     | | Confidence: High                             |   |                   |
|                     | +----------------------------------------------+   |                   |
|                     | Composer: Ask... [Ask] [Generate] [Safe Test]      |                   |
+---------------------+----------------------------------------------------+---------------------+
```

**Visual details:**

- Answer sections màu teal heading: `Allergies`, `Active Medications`, `Potential Risk`, `Recommendation`.
- Citations inline dạng `[1] [2] [3]` màu xanh.
- Risk bullets có clinical cautions: hyperkalemia, bleeding risk with colonoscopy, metformin eGFR warning.
- Evidence rail có 3 citation cards, mỗi card có thumbnail document và relevance dots.
- Footer assistant: `Assistive output — verify with clinical staff.` + confidence high.

**Components:** `CitedClinicalAnswer`, `InlineCitationLink`, `CitationCardWithThumbnail`, `ClinicalSafetyDisclaimer`.

---

# F. Chat

---

## 13. chat.landing.ai-hms-copilot

**PNG:** `chat.landing.ai-hms-copilot.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Chat / Landing / No patient selected`  
**Purpose:** entry point chung cho AI copilot khi chưa chọn patient context cụ thể.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+-----------------------+------------------------------------------------------------------------+
| Sidebar               | +--------------------------------------------------------------------+  |
| # Chat                | |                     [large friendly bot illustration]               |  |
| Recent Threads        | |                                                                    |  |
| - Anticoagulation     | |                  How can I help you today?                          |  |
| - Lab result          | | Ask questions, summarize records, review documents...               |  |
| - Discharge summary   | | +----------------+ +----------------+ +----------------+ +-------+ |  |
| - Medication reconcil.| | | Summarize rec. | | Review docs    | | Find insights | |Quick | |  |
| Permission card       | | +----------------+ +----------------+ +----------------+ +-------+ |  |
|                       | |                                                                    |  |
|                       | | +--------------------------------------------------------------+   |  |
|                       | | | Ask a clinical question or request information...           send|   |  |
|                       | | | [Ask] [Generate Summary] [Safe. Refusal Test]  Streaming ON   |   |  |
|                       | | +--------------------------------------------------------------+   |  |
|                       | +--------------------------------------------------------------------+  |
+-----------------------+------------------------------------------------------------------------+
```

**Visual details:**

- Main content là một large bordered panel centered, nhiều whitespace.
- Hero bot 3D/soft blue, title lớn.
- 4 suggestion cards ngang: `Summarize this record`, `Review recent documents`, `Find key insights`, `Generate a quick overview`.
- Composer lớn ở dưới, icon send góc phải; action buttons bên dưới input.
- Sidebar recent threads có danh sách 4 thread.

**Components:** `ChatLandingHero`, `SuggestionActionCard`, `ClinicalComposer`, `StreamingToggle`.

---

## 14. chat.workspace.new-patient-context-thread

**PNG:** `chat.workspace.new-patient-context-thread.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Chat / New clinical conversation / Patient context selected`  
**Purpose:** màn hình bắt đầu cuộc hội thoại mới với patient context `John Carter`, có prompt suggestions và right help rail.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+-----------------------------------------------------+--------------------+
| Sidebar             | Start a new clinical conversation                  | How this works     |
| # Chat              | Ask questions, get summaries...                    | - Ask anything     |
| Recent Threads      | [JC John Carter MRN 104582] [Authorized v]         | - Get cited answers|
| Permission card     | [General knowledge mode   toggle OFF]              | - Permission-aware |
|                     | +------------------------------------------------+  | - Built workflow   |
|                     | |                bot illustration                 |  | Tips for results   |
|                     | | Your AI clinical assistant is ready to help      |  | • Be specific      |
|                     | | Ask any question about this patient's care...    |  | • Provide context  |
|                     | | [Secure] [Citations] [Clinical workflows]        |  | Need help card     |
|                     | | Try asking me about John Carter                  |  | View user guide →  |
|                     | | +----------------+ +----------------+ +-------+ |  |                    |
|                     | | | Summarize      | | Allergies meds | | Labs  | |  |                    |
|                     | | | Discharge summ | | Search policies| |F/U   | |  |                    |
|                     | +------------------------------------------------+  |                    |
|                     | Composer: Ask... [Ask] [Generate Summary] [Safe]   |                    |
+---------------------+-----------------------------------------------------+--------------------+
```

**Visual details:**

- Top patient selector card + authorized chip.
- General knowledge mode toggle nằm trên cùng bên phải content, đang OFF.
- Center panel có bot illustration + 3 mini trust chips.
- Prompt grid 2×3: summarize, review allergies/meds, show latest labs, draft discharge summary, search policies, find follow-up actions.
- Right rail hướng dẫn gồm 5 block: how this works, tips, need help.

**Components:** `PatientSelector`, `GeneralKnowledgeToggle`, `PromptSuggestionGrid`, `HowItWorksRail`.

---

## 15. chat.answer.safe-refusal-insufficient-evidence

**PNG:** `chat.answer.safe-refusal-insufficient-evidence.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Chat / Safe refusal / Insufficient evidence`  
**Purpose:** từ chối trả lời khi không có evidence phù hợp trong dữ liệu được phép truy cập.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+----------------------------------------------------+---------------------+
| Sidebar             | [Patient: Maria Gonzalez MRN 103991] [Authorized] | Evidence & Citations|
| # Chat              | Safe Refusal / Insufficient Evidence              | No supporting       |
| Recent Threads      | User: What was the detailed MRI interpretation... | evidence found      |
| Permission card     | +----------------------------------------------+   | + What this means + |
|                     | | [purple shield] Insufficient evidence         |   | • info may not    |
|                     | | I'm unable to answer...                       |   |   exist           |
|                     | | I did not find any MRI interpretation...      |   | • outside perms   |
|                     | |                                                |   | • broaden/upload  |
|                     | | What you can do next:                         |   |                   |
|                     | | • Search the knowledge base                   |   | Retrieved but     |
|                     | | • Upload the MRI report                       |   | insufficient      |
|                     | | • Ask a narrower question                     |   | + MRI lumbar ...  |
|                     | | If you believe the document exists...         |   | + Knee MRI ...    |
|                     | | Confidence: Low                               |   | Can't find?       |
|                     | +----------------------------------------------+   | [Upload document]  |
|                     | [Search documents] [Upload a document] [Ask narrower question]           |
|                     | Composer with Ask / Generate Summary / Safe Refusal Test                 |
+---------------------+----------------------------------------------------+---------------------+
```

**Visual details:**

- Answer card header tím `Insufficient evidence`, icon shield.
- Explains not enough authorized evidence; không hallucinate.
- Next action buttons ngay dưới answer: `Search documents`, `Upload a document`, `Ask a narrower question`.
- Confidence chip `Low` màu cam.
- Right rail: illustration magnifier/document, title `No supporting evidence found`, explanatory card, 2 insufficient result cards.
- Insufficient cards ghi rõ document related nhưng không chứa requested interpretation / different body region.

**Components:** `SafeRefusalCard`, `NoEvidenceRail`, `RetrievedButInsufficientCard`, `RemediationActionButtons`.

---

# G. Citations & document viewer

---

## 16. citations.viewer.verified-source-document

**PNG:** `citations.viewer.verified-source-document.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Citation viewer / Verified source PDF modal`  
**Purpose:** xem tài liệu nguồn được trích dẫn, highlight snippet và verification metadata.

```ascii
+------------------------------------------------------------------------------------------------+
| Dimmed chat workspace background: Medication and allergy review                                  |
|                                                                                                |
|        +--------------------------------------------------------------------------------+      |
|        | [PDF icon] Allergy_History_0424.pdf [Clinical Note] [Download] [Open Source] | X |      |
|        | Patient John Carter | Source: EHR - Allergies                                 |      |
|        +--------------+---------------------------------------+-------------------------+      |
|        | Pages        | Toolbar: < 1 / 2 >  - 100% + full     | Citation Details        |      |
|        | 2 pages      |                                       | [Verified Source]       |      |
|        | +----------+ | +-----------------------------------+ | Document/file/page      |      |
|        | | page 1 * | | General Hospital                    | Chunk / Captured        |      |
|        | +----------+ | | Patient Allergy History            | Source / Accessed / By  |      |
|        | +----------+ | | Patient Name John Carter MRN...    |                         |      |
|        | | page 2   | | Allergies                          | Extracted Snippet       |      |
|        | +----------+ | | == Penicillin - rash (childhood)== | +---------------------+ |      |
|        |              | | == Iodinated contrast...        == | | snippet + relevance | |      |
|        |              | | No known food allergies            | +---------------------+ |      |
|        |              | | Allergy Details...                 | Verification            |      |
|        |              | +-----------------------------------+ | Source Integrity OK     |      |
|        |              |                                       | Permission Authorized   |      |
|        |              |                                       | Data Sensitivity PHI    |      |
|        +--------------+---------------------------------------+-------------------------+      |
|        | [shield] This document is from a trusted source and has not been altered. Learn... |      |
|        +--------------------------------------------------------------------------------+      |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Modal cực lớn phủ giữa, có 3 vùng: thumbnails, PDF canvas, citation detail panel.
- Background chat bị dim.
- Page thumbnail active có border xanh.
- PDF page có highlight vàng cho allergies.
- Citation details panel có chip `Verified Source`, metadata đầy đủ, snippet card, relevance dots, verification checklist.
- Footer trust bar có shield icon và link learn more.

**Components:** `DocumentViewerModal`, `PdfThumbnailRail`, `PdfToolbar`, `CitationDetailsPanel`, `VerificationChecklist`, `TrustedSourceFooter`.

---

# H. Documents & OCR

---

## 17. documents.dashboard.ocr-indexing-semantic-search

**PNG:** `documents.dashboard.ocr-indexing-semantic-search.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Documents & OCR / Dashboard`  
**Purpose:** quản lý upload/OCR/indexing documents và semantic search trên tài liệu lâm sàng.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+----------------------------------------------------------+---------------+
| Sidebar             | Documents & OCR                                         | Semantic      |
| # Documents         | Ingest, process, and search...                          | Search        |
| Recent Documents    | +----------------------------------------------------+   | [query][Search]|
| - Discharge summary | | Drag & drop files here...                         |   | Top matching  |
| - Lab results       | | [Upload PDF] [Upload Image] [Sync HMS Evidence]   |   | chunks        |
| - Cardiology note   | +----------------------------------------------------+   | 1 Medication  |
| Permission card     | +----------------------------------------------------+   | 2 Discharge   |
|                     | | Search documents... | Patient v | Type v | Status | |  | 3 Consult     |
|                     | +----------------------------------------------------+   | See all       |
|                     | Showing 1-10 of 48 documents                         | +-------------+|
|                     | +----------------------------------------------------+   | Processing    |
|                     | | Document Name | Patient | Type | Status | OCR | Date|  | Pipeline      |
|                     | | Discharge...  | John    | ...  |Indexed|98% | ... |  | Uploaded->OCR |
|                     | | Cardiology... | John    | Note |OCR Proc|72| ... |  | Chunked...    |
|                     | | Operative...  | John    | Note |Index Failed| |     | +-------------+|
|                     | +----------------------------------------------------+   | Storage Usage |
|                     | Pagination                                           | donut chart   |
+---------------------+----------------------------------------------------------+---------------+
```

**Visual details:**

- Dropzone lớn top-left dashed border xanh nhạt, icon upload cloud.
- 3 upload actions dạng buttons: PDF, Image, Sync HMS Evidence.
- Table columns: Document Name, Patient, Type, Status, OCR Confidence, Indexed At, Actions.
- Status chips: Indexed xanh, OCR Processing cam, Archived xám, Index Failed đỏ.
- Right rail: semantic search query `What medications is the patient currently taking?`, top matching chunks with confidence %, processing pipeline, storage & usage donut.
- Storage donut có breakdown: Documents, Images, OCR Text, Embeddings, Other.

**Components:** `DocumentUploadDropzone`, `DocumentsTable`, `SemanticSearchPanel`, `MatchingChunkCard`, `ProcessingPipelineCard`, `StorageUsageDonut`.

---

## 18. documents.ocr-review.needs-review-low-confidence

**PNG:** `documents.ocr-review.needs-review-low-confidence.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Documents / OCR Review / Low confidence`  
**Purpose:** review tài liệu OCR failed/low confidence trước khi approve & index.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+--------------------------------------------------------------------------+
| Sidebar             | ← Back to Documents                                                       |
| # Documents         | Document Review                         [Retry OCR] [Edit Metadata]       |
| Recent Documents    | Review and correct extracted content...  [Approve & Index] [Archive red]  |
| Permission card     | +--------------------------------------------------------------------+   |
|                     | | ! Low OCR confidence detected                                      X |   |
|                     | +--------------------------------------------------------------------+   |
|                     | +--------------------------------------------------------------------+   |
|                     | | [PDF] Outside_Referral_Scan_2025-05-11.pdf [OCR Failed]             |   |
|                     | | Maria Gonzalez | Uploaded... | Type: Referral Letter | Source...    |   |
|                     | +--------------------------------------------------------------------+   |
|                     | Tabs: Review | Metadata | Activity                                      |
|                     | +----------+ +-----------------------------+ +----------------------+   |
|                     | | Pages    | | Scanned document page       | | Extracted Text       |   |
|                     | | page 1 * | | highlighted low-confidence  | | [Low confidence]    |   |
|                     | | page 2   | | medications highlighted     | | OCR text with red   |   |
|                     | | + Add    | |                             | | uncertain tokens    |   |
|                     | +----------+ +-----------------------------+ +----------------------+   |
|                     |                                  +-----------------+ +--------------+   |
|                     |                                  | Processing      | | Failure      |   |
|                     |                                  | Timeline        | | Reasons      |   |
|                     |                                  | uploaded ✓      | | 4 warnings   |   |
|                     |                                  | OCR failed ✕    | | Checklist    |   |
|                     |                                  | pending steps   | | 0/4 complete |   |
+---------------------+--------------------------------------------------------------------------+
```

**Visual details:**

- Red alert banner top: `Low OCR confidence detected`.
- Document header card có filename, chip `OCR Failed`, patient, type, uploaded date, source.
- Main review area chia 3: page thumbnails, scanned document image, extracted text panel.
- Low confidence highlights màu đỏ/rose trên document và extracted text.
- Right side cards: Processing Timeline, Failure Reasons, Review Checklist.
- Top actions gồm retry, edit metadata, approve & index primary xanh, archive destructive đỏ.

**Components:** `OCRReviewPage`, `LowConfidenceBanner`, `DocumentReviewHeader`, `ScannedPagePane`, `ExtractedTextPane`, `ProcessingTimeline`, `FailureReasonsCard`, `ReviewChecklist`.

---

## 19. documents.upload.batch-ocr-progress-modal

**PNG:** `documents.upload.batch-ocr-progress-modal.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Documents / Upload / Batch OCR progress modal`  
**Purpose:** upload nhiều file, theo dõi progress từng file và pipeline OCR/index.

```ascii
+------------------------------------------------------------------------------------------------+
| Dimmed Documents & OCR dashboard background                                                     |
|                                                                                                |
|               +----------------------------------------------------------------+               |
|               | [upload icon] Upload Documents & OCR                       X   |               |
|               | Upload files to extract text, structure data...                |               |
|               | +----------------------------------------------------------+   |               |
|               | | Drag & drop files here, or browse                       |   |               |
|               | | Supports PDF, PNG, JPG, TIFF, DICOM                     |   |               |
|               | | [Browse files]  Up to 50 files • Max 200 MB per file    |   |               |
|               | +----------------------------------------------------------+   |               |
|               | 3 files selected (245.7 MB)                       Remove all |               |
|               | +----------------------------------------------------------+   |               |
|               | | File Name | Patient | Size | Status | Progress          |   |               |
|               | | Discharge... | John |2.4MB | Ready to index | 100% ✓ |   |               |
|               | | Lab Results | John |12.8MB| Uploading      | 65%    |   |               |
|               | | Cardiology...| John |4.7MB | Needs review   | 20% !  |   |               |
|               | +----------------------------------------------------------+   |               |
|               | Pipeline: Uploading ●──OCR Parsing○──Chunking○──Embedding○──Ready○ |        |
|               | [Add more files]                              [Cancel] [Continue →] |        |
|               | + Secure ingestion & audit logging | Audit enabled | Region US East |        |
|               +----------------------------------------------------------------+               |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Modal rộng, dropzone ở đầu, file table ở giữa, pipeline stepper dưới.
- 3 file trạng thái khác nhau: ready to index, uploading, needs review.
- Progress bars: xanh 100%, xanh/blue 65%, cam 20%.
- Secure footer có shield icon, audit logging enabled, data region `US East (Ohio)`.
- CTA `Continue` primary, `Cancel` secondary, `Add more files` outline.

**Components:** `BatchUploadModal`, `UploadDropzoneCompact`, `UploadFileTable`, `OCRPipelineStepper`, `SecureIngestionFooter`.

---

# I. Metrics

---

## 20. metrics.dashboard.impact-quality-summary

**PNG:** `metrics.dashboard.impact-quality-summary.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Metrics / Impact & Quality Summary`  
**Purpose:** theo dõi hiệu quả AI assistant: lookup time, time saved, cited answer rate, denied audit count, quality/safety, feedback.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+---------------------+--------------------------------------------------------------------------+
| Sidebar             | Metrics & Impact                       [Apr 13 - May 10, 2025 v] [Filter] |
| # Metrics           | Track performance, adoption...                 [All metrics synthetic]    |
| Recent Threads      | +---------+ +---------+ +---------+ +---------+                         |
| Permission card     | | Lookup  | | Time    | | Cited   | | Denied  |                         |
|                     | | 4.2 sec | | 13.6min | | 94.7%   | | 2       |                         |
|                     | +---------+ +---------+ +---------+ +---------+                         |
|                     | +------------------------------+ +------------------+ +---------------+ |
|                     | | Lookup Time Before vs After  | | Daily Query Vol. | | Quality/Safe | |
|                     | | line chart, 76% reduction    | | bar chart        | | area + line   | |
|                     | +------------------------------+ +------------------+ +---------------+ |
|                     | note: time metrics compare baseline...                                   |
|                     | +-----------------------------------------------+ +------------------+ |
|                     | | Workflow Impact table                         | | User Feedback    | |
|                     | | Patient Summary 8.4 -> 2.1, saved 6.3, 75%   | | Rating 4.7/5     | |
|                     | | Document Search ...                           | | 3 feedback quotes| |
|                     | +-----------------------------------------------+ +------------------+ |
+---------------------+--------------------------------------------------------------------------+
```

**Visual details:**

- KPI cards đầu: Avg Lookup Time, Time Saved per Query, Cited Answer Rate, Denied Audit Count.
- Date range filter ở top-right và info pill synthetic/demo data.
- Charts: line comparison trước/sau AI, daily bar chart, answer quality/safety line/area chart.
- Workflow table: patient summary, document search, medication review, discharge summary với baseline/actual/time saved/improvement bar.
- User feedback card: large `4.7/5`, star rating, quote list với helpful chip.

**Components:** `MetricsHeader`, `MetricSummaryCard`, `LineComparisonChart`, `BarVolumeChart`, `QualitySafetyChart`, `WorkflowImpactTable`, `UserFeedbackCard`.

---

# J. Additional analyzed screens (+5)

Các màn hình dưới đây được bổ sung từ 5 PNG mới. Khác với nhóm “proposed screens” cũ, đây là các màn hình/overlay thực tế đã có UI, có mô tả chi tiết để dựng lại bằng component instance trong Figma.

---

## 21. patients.overview.ai-summary-hms-snapshot

**PNG:** `patients.overview.ai-summary-hms-snapshot.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Patients / Patient Detail / Overview / AI-generated snapshot`  
**Purpose:** trang hồ sơ tổng quan cho một bệnh nhân đã được authorize. Màn hình kết hợp patient identity header, tab navigation, AI-generated patient summary, clinical citations inline và right rail tóm tắt rủi ro, thuốc, labs, encounters.

```ascii
+------------------------------------------------------------------------------------------------+
| Logo/Product | Global search....................................[⌘K] | Synthetic Data | User   |
+----------------------+-----------------------------------------------------------------------------+
| Sidebar              | ← Back to Patients                                                            |
| # Patients           | +------------------------------------------------------------+ +-------------+|
| Recent Patients      | | [JC] John Carter (MRN 104582)                 [Authorized] | | Allergy     ||
|  John Carter active  | | DOB | Sex | Phone | MRN | Blood Type                    | | Alerts      ||
|  Maria Gonzalez      | | Dept | Attending | Admission | Admitted | Room/Bed       | | Penicillin  ||
|  Robert Johnson      | +------------------------------------------------------------+ | Contrast    ||
| Permission card      | | Overview | Summary | Medications | Allergies | Labs | Docs | +-------------+|
|                      | +------------------------------------------------------------+ +-------------+|
|                      | | AI-Generated Patient Summary             [Confidence High] | | Current     ||
|                      | | Generated: May 10, 2025, 9:18 AM                         | | Medications ||
|                      | | +--------------------------------------------------------+ | | Lisinopril  ||
|                      | | | Clinical History                                     | | | Metoprolol ||
|                      | | | Current Medications                                  | | | Furosemide ||
|                      | | | Allergies                                             | | +-------------+|
|                      | | | Recent Labs horizontal mini-table                    | | +-------------+|
|                      | | | Follow-up Notes                                      | | | Latest Labs ||
|                      | | +--------------------------------------------------------+ | | Cr/eGFR/etc ||
|                      | | AI-generated content may contain errors. [View Sources]  | | +-------------+|
|                      | +------------------------------------------------------------+ +-------------+|
|                      | [Generate New Summary]                         Last updated   | | Encounters  ||
|                      |                                                            | | timeline    ||
+----------------------+------------------------------------------------------------+---------------+
```

**Visual details:**

- Patient header là card ngang lớn, có avatar initials `JC`, tên `John Carter`, MRN inline, chip `Authorized`, bookmark icon và kebab menu.
- Metadata header chia 2 hàng: DOB/Sex/Phone/MRN/Blood Type và Department/Attending Physician/Admission Status/Admitted On/Room-Bed.
- Tab bar dưới header dùng icon + label; `Overview` active bằng underline xanh và text xanh.
- Summary card là card lớn, border nhẹ, radius 16, nền trắng; title có sparkle icon xanh.
- Nội dung AI summary chia thành các section có icon tile trái: `Clinical History`, `Current Medications`, `Allergies`, `Recent Labs`, `Follow-up Notes`.
- Citations inline dạng `[1] [2] ... [10]` màu xanh; link `View Sources (10)` ở footer card.
- Right rail là stack 4 card: allergy alerts đỏ nhạt, current meds, latest labs, upcoming/recent encounters.
- Labs hiển thị dạng compact table, mỗi row có value, timestamp nhỏ, status chip `High/Low/Normal`.
- Encounters card dùng vertical timeline với status chips `Active`, `Completed`, `Scheduled`.
- Primary CTA dưới card: `Generate New Summary`; bên phải có `Last updated` và refresh icon.

**Components:** `PatientDetailHeader`, `PatientMetadataGrid`, `PatientDetailTabs`, `AIGeneratedSummaryCard`, `ClinicalSummarySection`, `InlineCitationLink`, `MiniLabStrip`, `ClinicalRightRail`, `AllergyAlertsCard`, `CurrentMedicationListCard`, `LatestLabsCard`, `EncounterTimelineCard`.

**Figma notes:**

- Use `Shell/Standard`. Main content uses 2-column grid: left content ~744 px, right rail ~340 px, gap 24 px.
- Build header and right rail as reusable instances; do not create row text manually.
- AI summary content should be Auto Layout vertical with section rows; mini lab strip uses equal-width cells.

---

## 22. search.global.command-palette-recent-entities

**PNG:** `search.global.command-palette-recent-entities.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Global Search / Command Palette / Recent entities`  
**Purpose:** overlay command palette khi người dùng bấm global search hoặc `⌘K`, cho phép tìm nhanh patients, documents, threads và chạy quick commands.

```ascii
+------------------------------------------------------------------------------------------------+
| Dimmed dashboard background                                                                      |
|                                                                                                |
|                              +----------------------------------------------+                  |
|                              | [search icon] Search patients...       [⌘K] |                  |
|                              +----------------------------------------------+                  |
|                              | Recent Patients                 View all →   |                  |
|                              | [JC] John Carter     MRN 104582       Open ↵ |                  |
|                              | [ED] Emily Davis     MRN 107331       Open ↵ |                  |
|                              | [ML] Michael Lee     MRN 102773       Open ↵ |                  |
|                              |----------------------------------------------|                  |
|                              | Recent Documents               View all →    |                  |
|                              | [pdf] Discharge Summary...            Open ↵ |                  |
|                              | [pdf] Lab Results...                  Open ↵ |                  |
|                              | [pdf] Cardiology Consult...           Open ↵ |                  |
|                              |----------------------------------------------|                  |
|                              | Quick Commands                               |                  |
|                              | [sparkle] Start new clinical conversation  ↵ |                  |
|                              | [doc] Generate patient summary             ↵ |                  |
|                              | [upload] Upload document                  ⌘U |                  |
|                              | [shield] Open audit logs                ⇧⌘A |                  |
|                              | [chart] View metrics                    ⇧⌘M |                  |
|                              |----------------------------------------------|                  |
|                              | Recent Threads                  View all →   |                  |
|                              | [chat] Discharge summary...          Open ↵ |                  |
|                              | [chat] Lab result follow-up...       Open ↵ |                  |
|                              | Tip: Use ↑↓ to navigate, ↵ to open, ⌘K close|
|                              +----------------------------------------------+                  |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Toàn bộ dashboard phía sau bị dim overlay màu navy/gray opacity khoảng 50–60%.
- Palette nằm center-top, không chính giữa tuyệt đối; top offset khoảng 118 px.
- Panel trắng radius 16–18, shadow modal, width khoảng 704 px.
- Search input ở đầu panel có border xanh focus, icon search trái, shortcut chip `⌘K` phải.
- Mỗi section có title trái và link `View all ... →` phải.
- Entity rows dùng avatar/icon trái, title strong, metadata muted ở dòng 2, action `Open` + keycap phải.
- Quick Commands dùng icon tile pastel, title + subtitle, shortcut keycap phải.
- Footer tips nằm trong vùng nền nhạt, có icon bulb và hướng dẫn phím.

**Components:** `CommandPaletteOverlay`, `CommandSearchInput`, `CommandSection`, `CommandEntityRow`, `CommandActionRow`, `KeyboardHint`, `SearchBackdrop`.

**Figma notes:**

- Treat this as overlay state: `Backdrop` z=500, `CommandPalette` z=600.
- Palette content uses vertical Auto Layout, section dividers, row height 42–48 px.
- Row component must support variants: `type=patient|document|command|thread`, `shortcut=true/false`, `metadata=single|double`.

---

## 23. workspaces.environment-selector.synthetic-sandbox-training-production

**PNG:** `workspaces.environment-selector.synthetic-sandbox-training-production.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Topbar / Environment selector / Synthetic Data menu open`  
**Purpose:** dropdown chọn môi trường dữ liệu. UI nhấn mạnh người dùng đang ở Synthetic Data, có các lựa chọn Sandbox, Training Mode và Production Data bị hạn chế.

```ascii
+------------------------------------------------------------------------------------------------+
| Wide dashboard background                                                                       |
|                                               [Synthetic Data ▲] [shield] [User]                |
|                                                     +--------------------------------------+   |
|                                                     | [db] Synthetic Data       [Current] |   |
|                                                     |      Demo environment with synthetic|   |
|                                                     |                                      |   |
|                                                     | [flask] Sandbox        [Isolated]   |   |
|                                                     |        Isolated testing environment |   |
|                                                     |                                      |   |
|                                                     | [cap] Training Mode    [Training]   |   |
|                                                     |       Training and evaluation env.  |   |
|                                                     |                                      |   |
|                                                     | [lock] Production Data [Restricted] |   |
|                                                     |        Restricted live environment  |   |
|                                                     |--------------------------------------|   |
|                                                     | (i) You are currently working in... |   |
|                                                     +--------------------------------------+   |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Dropdown anchored ngay dưới pill `Synthetic Data` ở topbar; pill đang active có chevron up.
- Panel trắng, radius 12–16, shadow, width khoảng 370 px.
- Mỗi option là row cao 56–64 px, icon màu riêng: database xanh, flask cam, graduation cap tím, lock đỏ.
- `Synthetic Data` có green check nhỏ và chip `Current` xanh.
- `Sandbox` có chip `Isolated` xám; `Training Mode` có chip tím; `Production Data` có chip đỏ `Restricted`.
- Footer info có divider, icon info và mô tả “Changes are isolated to this environment.”
- Không có backdrop; dashboard vẫn sáng bình thường.

**Components:** `EnvironmentTrigger`, `EnvironmentSelectorPopover`, `EnvironmentOptionRow`, `EnvironmentStatusChip`, `PopoverInfoFooter`.

**Figma notes:**

- Anchor to `WideTopbar.EnvironmentPill`; panel top = trigger bottom + 8 px.
- Dropdown z-index = `z.dropdown`, no modal backdrop.
- Use fixed width 370 px; internal padding 18–20 px; row gap 12–16 px.

---

## 24. users.preferences.profile-security-system-status

**PNG:** `users.preferences.profile-security-system-status.png`  
**Canvas:** 1448 × 1086  
**Route/state:** `Settings / Profile / Preferences + Security`  
**Purpose:** trang cài đặt tài khoản, preference, display, security, system status và usage. Đây là settings page trong app shell, không phải modal.

```ascii
+------------------------------------------------------------------------------------------------+
| Topbar                                                                                          |
+----------------------+----------------------------------------------------------+-------------+
| Sidebar              | Settings                                                | Account     |
| # Settings           | Manage your account, preferences...                     | Summary     |
| Recent Threads       | +----------------+ +----------------------------------+ | Active      |
| Permission card      | | Settings menu  | | Profile                          | | Role        |
|                      | | # Profile      | | [avatar] Dr. Sarah Chen [Verified]| | Department  |
|                      | | Notifications  | | email / phone / Edit Profile      | | Account ID  |
|                      | | AI Preferences | +----------------------------------+ +-------------+
|                      | | Display        | | Preferences                      | | System      |
|                      | | Security       | | Default startup page     [select] | | Status      |
|                      | | Integrations   | | Show citations default   [toggle] | | Operational |
|                      | | Data Privacy   | | Enable streaming        [toggle] | +-------------+
|                      | | Billing        | | Patient context         [select] | | Usage       |
|                      | | Advanced       | | Language / Date format / TZ       | | This Month  |
|                      | +----------------+ +----------------------------------+ | bars        |
|                      |                  | Display: Theme + Density           | +-------------+
|                      |                  | Security: timeout/MFA/sessions     | | Need Help   |
+----------------------+----------------------------------------------------------+-------------+
```

**Visual details:**

- App shell standard; sidebar main active item `Settings`.
- Page content có local settings subnav bên trái với các mục: Profile, Notifications, AI Preferences, Display, Security, Integrations, Data & Privacy, Billing, Advanced.
- Local subnav active item `Profile` có nền xanh nhạt, icon và text xanh.
- Main column gồm sections: Profile card, Preferences card, Display card, Security card.
- Profile card có avatar lớn, tên `Dr. Sarah Chen`, chip `Verified`, specialty/role, email/phone, button `Edit Profile`.
- Preferences card là list rows có select/toggle: Default startup page, citations default, streaming, patient context, language, date/time, timezone.
- Display card có segmented controls: Theme `Light/Dark/System`, Density `Comfortable/Compact/Spacious`; selected có border xanh và nền xanh nhạt.
- Security card có session timeout select, MFA enabled row, active sessions row.
- Right rail gồm 4 card: Account Summary, System Status, Usage This Month, Need Help.

**Components:** `SettingsPageLayout`, `SettingsLocalNav`, `ProfileSummaryCard`, `PreferenceRow`, `ToggleSwitch`, `SegmentedControl`, `SecuritySettingsCard`, `AccountSummaryCard`, `SystemStatusCard`, `UsageProgressCard`, `NeedHelpCard`.

**Figma notes:**

- Use 3-column content: local nav ~176 px, main column ~574 px, right rail ~300 px.
- Settings rows use consistent 52 px row height; toggles align right.
- Right rail card stack uses 16 px gap and fixed card width.

---

## 25. dashboard.overview.success-toast-stack

**PNG:** `dashboard.overview.success-toast-stack.png`  
**Canvas:** 1672 × 941  
**Route/state:** `Dashboard / Populated / Success toast stack`  
**Purpose:** dashboard populated sau khi user hoàn thành actions; hiển thị toast notifications dạng stack ở góc phải dưới.

```ascii
+------------------------------------------------------------------------------------------------+
| Wide dashboard overview                                                                         |
|                                                                                                |
| [Sidebar]  Dashboard KPI cards, task panel, recent patients, right cards, charts...             |
|                                                                                                |
|                                                                                  +-----------+ |
|                                                                                  | ✓ Request | |
|                                                                                  | submitted| |
|                                                                                  |     [x]   | |
|                                                                                  +-----------+ |
|                                                                                  +-----------+ |
|                                                                                  | ✓ Settings| |
|                                                                                  | saved [x] | |
|                                                                                  +-----------+ |
+------------------------------------------------------------------------------------------------+
```

**Visual details:**

- Base dashboard là populated wide layout, không bị dim.
- Toast stack anchored bottom-right, above footer/safe area; các toast nổi trên content bằng shadow card.
- Mỗi toast có nền xanh rất nhạt, border xanh nhạt, icon check trong circle xanh, message strong, close icon phải.
- Toast đầu: `Request submitted successfully`; toast thứ hai: `Settings saved`.
- Stack gap khoảng 12 px; toast width khoảng 290–300 px, height 56–64 px.
- Z-index cao hơn content nhưng thấp hơn modal; không chặn tương tác toàn màn hình.

**Components:** `ToastStack`, `ToastNotification`, `ToastIcon`, `ToastCloseButton`.

**Figma notes:**

- Toast stack uses fixed position: right 24–32 px, bottom 24–32 px.
- Use Auto Layout vertical reverse or normal stack with newest toast on top.
- Do not bake toast into dashboard cards; toast is a global overlay layer under `Overlays/ToastStack`.


# K. Screen inventory summary

| # | Screen ID | Module | Visible state |
|---:|---|---|---|
| 1 | access-control.denied.no-treatment-relationship | Access Control | Access denied, no treatment relationship |
| 2 | access-requests.create.clinical-justification-modal | Access Requests | Create request modal |
| 3 | audit.logs.access-event-detail-panel | Audit | Table + selected event drawer |
| 4 | auth.login.staff-sso-email-password | Auth | Login split with SSO/email |
| 5 | auth.mfa.verify-identity-code | Auth | MFA OTP verification |
| 6 | dashboard.empty.workspace-onboarding-first-data | Dashboard | Empty workspace onboarding |
| 7 | dashboard.overview.action-success-toast | Dashboard | Populated dashboard base state / prior toast-state capture |
| 8 | dashboard.overview.populated-hms-ai-workspace | Dashboard | Populated dashboard + charts |
| 9 | patients.empty.no-results-or-no-access | Patients | Empty/no patients found |
| 10 | patients.list.scoped-alerts-recent-activity | Patients | Scoped patient list + right rail |
| 11 | patients.ai-summary.stream-citations-retrieving | Chat/Patients | Streaming summary + citation retrieval |
| 12 | patients.medication-review.cited-safety-answer | Chat/Patients | Completed cited safety answer |
| 13 | chat.landing.ai-hms-copilot | Chat | General copilot landing |
| 14 | chat.workspace.new-patient-context-thread | Chat | New patient-context thread |
| 15 | chat.answer.safe-refusal-insufficient-evidence | Chat | Safe refusal/insufficient evidence |
| 16 | citations.viewer.verified-source-document | Citations | Verified PDF source modal |
| 17 | documents.dashboard.ocr-indexing-semantic-search | Documents | OCR dashboard + semantic search |
| 18 | documents.ocr-review.needs-review-low-confidence | Documents | Low OCR confidence review |
| 19 | documents.upload.batch-ocr-progress-modal | Documents | Batch upload/OCR progress modal |
| 20 | metrics.dashboard.impact-quality-summary | Metrics | Impact/quality dashboard |
| 21 | patients.overview.ai-summary-hms-snapshot | Patients | Patient detail overview + AI summary snapshot |
| 22 | search.global.command-palette-recent-entities | Global Search | Command palette + recent entities/commands |
| 23 | workspaces.environment-selector.synthetic-sandbox-training-production | Workspace | Environment selector dropdown |
| 24 | users.preferences.profile-security-system-status | Settings | Profile/preferences/security + system status |
| 25 | dashboard.overview.success-toast-stack | Dashboard | Populated dashboard + success toast stack |

---

# L. Component reuse map

```ascii
AppShell
 ├─ Topbar
 ├─ SidebarNav
 ├─ PermissionAwareSidebarCard
 └─ FooterDisclaimer

Clinical Context
 ├─ PatientContextChip
 ├─ PermissionStatusChip
 ├─ PatientSummaryStrip
 └─ ClinicalSafetyDisclaimer

AI Chat
 ├─ ChatComposer
 ├─ UserMessageBubble
 ├─ AssistantAnswerCard
 ├─ StreamingAnswerCard
 ├─ SafeRefusalCard
 └─ PromptSuggestionGrid

Evidence
 ├─ EvidenceRail
 ├─ CitationCard
 ├─ CitationLoadingCard
 ├─ NoEvidenceRail
 ├─ DocumentViewerModal
 └─ CitationDetailsPanel

Documents/OCR
 ├─ DocumentUploadDropzone
 ├─ DocumentsTable
 ├─ BatchUploadModal
 ├─ OCRReviewPage
 ├─ ProcessingPipelineCard
 └─ SemanticSearchPanel

Admin/Compliance
 ├─ AuditEventsTable
 ├─ AuditEventDrawer
 ├─ AccessDeniedPanel
 ├─ AccessRequestModal
 └─ AccessRequestReviewDrawer

Analytics
 ├─ MetricCard
 ├─ TrendLineChartCard
 ├─ BarVolumeChartCard
 ├─ WorkflowImpactTable
 └─ UserFeedbackCard

Patient Detail & Settings
 ├─ PatientDetailHeader
 ├─ PatientDetailTabs
 ├─ AIGeneratedSummaryCard
 ├─ SettingsLocalNav
 ├─ PreferenceRow
 ├─ SegmentedControl
 └─ UsageProgressCard

Global Overlays
 ├─ CommandPaletteOverlay
 ├─ EnvironmentSelectorPopover
 ├─ ToastStack
 └─ ToastNotification
```
