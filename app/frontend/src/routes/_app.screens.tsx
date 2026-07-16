import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/_app/screens")({
  head: () => ({ meta: [{ title: "Screen index — HMS AI Copilot" }] }),
  component: ScreensIndex,
});

type Item = {
  id: string;
  title: string;
  href: string;
  priority: "MVP" | "Should" | "Could" | "Phase 2";
};
type Group = { label: string; items: Item[] };

const groups: Group[] = [
  {
    label: "Authentication",
    items: [
      { id: "AUTH-001", title: "Login", href: "/auth/login", priority: "MVP" },
      { id: "AUTH-002", title: "MFA verify", href: "/auth/mfa", priority: "MVP" },
      {
        id: "AUTH-003",
        title: "Forgot password",
        href: "/auth/forgot-password",
        priority: "Should",
      },
      { id: "AUTH-004", title: "Session expired", href: "/auth/session-expired", priority: "MVP" },
      { id: "AUTH-005", title: "SSO callback", href: "/auth/sso/callback", priority: "Should" },
    ],
  },
  {
    label: "Global",
    items: [
      { id: "GLOBAL-003", title: "Notifications", href: "/notifications", priority: "Should" },
      { id: "GLOBAL-006", title: "Keyboard shortcuts", href: "/help/shortcuts", priority: "Could" },
    ],
  },
  {
    label: "Dashboard",
    items: [
      { id: "DASH-002", title: "Overview", href: "/dashboard", priority: "MVP" },
      { id: "DASH-001", title: "Empty workspace", href: "/dashboard?state=empty", priority: "MVP" },
      {
        id: "DASH-003",
        title: "System degraded",
        href: "/dashboard?state=degraded",
        priority: "MVP",
      },
      { id: "DASH-004", title: "Customize", href: "/dashboard/customize", priority: "Could" },
      { id: "DASH-005", title: "Activity feed", href: "/dashboard/activity", priority: "Should" },
    ],
  },
  {
    label: "Patients",
    items: [
      { id: "PAT-002", title: "Patients list", href: "/patients", priority: "MVP" },
      {
        id: "PAT-003",
        title: "Overview & AI summary",
        href: "/patients/11111111-1111-1111-1111-111111111111/overview",
        priority: "MVP",
      },
      { id: "PAT-004", title: "Timeline", href: "/patients/11111111-1111-1111-1111-111111111111/timeline", priority: "Should" },
      { id: "PAT-005", title: "Documents", href: "/patients/11111111-1111-1111-1111-111111111111/documents", priority: "MVP" },
      { id: "PAT-006", title: "Labs & vitals", href: "/patients/11111111-1111-1111-1111-111111111111/labs", priority: "Should" },
      {
        id: "PAT-007",
        title: "Medications & allergies",
        href: "/patients/11111111-1111-1111-1111-111111111111/medications",
        priority: "MVP",
      },
      {
        id: "PAT-008",
        title: "Access history",
        href: "/patients/11111111-1111-1111-1111-111111111111/access-history",
        priority: "Should",
      },
      {
        id: "PAT-010",
        title: "Snapshot refresh",
        href: "/patients/11111111-1111-1111-1111-111111111111/refresh",
        priority: "Should",
      },
      { id: "PAT-009", title: "Not found", href: "/patients/missing/not-found", priority: "MVP" },
    ],
  },
  {
    label: "Access Control",
    items: [
      {
        id: "ACC-001",
        title: "Access denied",
        href: "/patients/33333333-3333-3333-3333-333333333333/access-denied",
        priority: "MVP",
      },
      {
        id: "ACC-003",
        title: "Request submitted",
        href: "/access-requests/ar-001",
        priority: "MVP",
      },
      { id: "ACC-004", title: "Requests inbox", href: "/access-requests", priority: "Should" },
      {
        id: "ACC-005",
        title: "Request review",
        href: "/access-requests/ar-001/review",
        priority: "Should",
      },
      { id: "ACC-006", title: "Access policy", href: "/access-policy", priority: "Should" },
    ],
  },
  {
    label: "Chat",
    items: [
      { id: "CHAT-001", title: "Chat landing", href: "/chat", priority: "MVP" },
      { id: "CHAT-002", title: "New patient context", href: "/chat/new", priority: "MVP" },
      {
        id: "CHAT-003",
        title: "Streaming",
        href: "/chat/patients/11111111-1111-1111-1111-111111111111?state=streaming",
        priority: "MVP",
      },
      { id: "CHAT-004", title: "Cited answer", href: "/chat/patients/11111111-1111-1111-1111-111111111111", priority: "MVP" },
      {
        id: "CHAT-005",
        title: "Safe refusal",
        href: "/chat/patients/11111111-1111-1111-1111-111111111111?state=refusal",
        priority: "MVP",
      },
      {
        id: "CHAT-006",
        title: "Permission blocked",
        href: "/chat/patients/11111111-1111-1111-1111-111111111111?state=forbidden",
        priority: "MVP",
      },
      {
        id: "CHAT-007",
        title: "LLM offline",
        href: "/chat/patients/11111111-1111-1111-1111-111111111111?state=llm-offline",
        priority: "MVP",
      },
      {
        id: "CHAT-008",
        title: "Rate limited",
        href: "/chat/patients/11111111-1111-1111-1111-111111111111?state=rate-limited",
        priority: "Should",
      },
      { id: "CHAT-009", title: "Thread history", href: "/chat/history", priority: "Should" },
      { id: "CHAT-010", title: "Prompt templates", href: "/chat/templates", priority: "Could" },
      { id: "CHAT-012", title: "General mode", href: "/chat/general", priority: "Should" },
    ],
  },
  {
    label: "Citations",
    items: [
      { id: "CITE-001", title: "Source viewer", href: "/citations/c-001", priority: "MVP" },
      {
        id: "CITE-002",
        title: "Side-by-side compare",
        href: "/citations/compare",
        priority: "Could",
      },
      {
        id: "CITE-003",
        title: "Missing source",
        href: "/citations/c-001?state=missing",
        priority: "MVP",
      },
      {
        id: "CITE-004",
        title: "Integrity warning",
        href: "/citations/c-001?state=integrity-warning",
        priority: "Should",
      },
    ],
  },
  {
    label: "Documents & OCR",
    items: [
      { id: "DOC-001", title: "Documents dashboard", href: "/documents", priority: "MVP" },
      { id: "DOC-002", title: "Batch upload", href: "/documents/upload", priority: "MVP" },
      { id: "DOC-003", title: "Document detail", href: "/documents/d-04", priority: "MVP" },
      {
        id: "DOC-004",
        title: "Low-confidence review",
        href: "/documents/d-09/review",
        priority: "MVP",
      },
      { id: "DOC-005", title: "Retry OCR", href: "/documents/d-09/retry", priority: "MVP" },
      { id: "DOC-006", title: "Semantic search", href: "/documents/search", priority: "MVP" },
      { id: "DOC-007", title: "Sync from HMS", href: "/documents/sync-hms", priority: "Should" },
      { id: "DOC-008", title: "Metadata edit", href: "/documents/d-04/edit", priority: "Should" },
      { id: "DOC-009", title: "Duplicates", href: "/documents/duplicates", priority: "Could" },
      { id: "DOC-010", title: "OCR queue", href: "/documents/ocr-queue", priority: "Should" },
    ],
  },
  {
    label: "Audit & Compliance",
    items: [
      { id: "AUD-001", title: "Audit logs", href: "/audit", priority: "MVP" },
      { id: "AUD-002", title: "Raw event JSON", href: "/audit/a-001/raw", priority: "Should" },
      { id: "AUD-003", title: "Denied attempts", href: "/audit/denied", priority: "MVP" },
      { id: "AUD-004", title: "Export", href: "/audit/export", priority: "Should" },
      { id: "AUD-005", title: "Trace timeline", href: "/audit/traces/tr-001", priority: "Should" },
      {
        id: "AUD-006",
        title: "Compliance summary",
        href: "/audit/compliance-summary",
        priority: "Could",
      },
    ],
  },
  {
    label: "Metrics",
    items: [
      { id: "MET-001", title: "Impact dashboard", href: "/metrics", priority: "MVP" },
      { id: "MET-002", title: "Workflow impact", href: "/metrics/workflows", priority: "MVP" },
      { id: "MET-003", title: "Citation quality", href: "/metrics/citations", priority: "Should" },
      { id: "MET-004", title: "Safe refusal", href: "/metrics/safe-refusal", priority: "Should" },
      { id: "MET-005", title: "Feedback", href: "/metrics/feedback", priority: "Could" },
      { id: "MET-006", title: "Cost saving config", href: "/metrics/config", priority: "Should" },
    ],
  },
  {
    label: "Timeline & Graph RAG",
    items: [
      { id: "TIME-001", title: "Clinical timeline", href: "/timeline", priority: "Should" },
      { id: "TIME-002", title: "Event detail", href: "/timeline/te-001", priority: "Could" },
      {
        id: "GRAPH-001",
        title: "Patient graph",
        href: "/graph/patients/11111111-1111-1111-1111-111111111111",
        priority: "Phase 2",
      },
      {
        id: "GRAPH-002",
        title: "Path evidence",
        href: "/graph/path/path-001",
        priority: "Phase 2",
      },
    ],
  },
  {
    label: "Medication Safety",
    items: [
      {
        id: "MED-001",
        title: "Med-allergy pre-check",
        href: "/patients/11111111-1111-1111-1111-111111111111/medication-review",
        priority: "Phase 2",
      },
      {
        id: "MED-002",
        title: "Conflict rule detail",
        href: "/medication-conflicts/c-001",
        priority: "Phase 2",
      },
      {
        id: "MED-003",
        title: "Pharmacist review queue",
        href: "/pharmacy/review-queue",
        priority: "Phase 2",
      },
    ],
  },
  {
    label: "Integrations & Ops",
    items: [
      { id: "INT-001", title: "HMS sync status", href: "/integrations/hms", priority: "MVP" },
      {
        id: "INT-002",
        title: "Manual patient sync",
        href: "/integrations/hms/patients/11111111-1111-1111-1111-111111111111/sync",
        priority: "MVP",
      },
      {
        id: "INT-003",
        title: "Sync job detail",
        href: "/integrations/hms/jobs/j-001",
        priority: "MVP",
      },
      { id: "INT-004", title: "DLQ", href: "/integrations/hms/dlq", priority: "Should" },
      {
        id: "INT-005",
        title: "OTel trace viewer",
        href: "/integrations/traces/tr-001",
        priority: "Should",
      },
      {
        id: "INT-006",
        title: "Vector index",
        href: "/integrations/vector-index",
        priority: "Should",
      },
      { id: "INT-007", title: "LLM runtime", href: "/integrations/llm", priority: "Should" },
    ],
  },
  {
    label: "Settings & Admin",
    items: [
      { id: "SET-001", title: "Profile", href: "/settings/profile", priority: "MVP" },
      { id: "SET-002", title: "AI preferences", href: "/settings/ai", priority: "MVP" },
      { id: "SET-003", title: "Display", href: "/settings/display", priority: "Should" },
      { id: "SET-004", title: "Security", href: "/settings/security", priority: "Should" },
      { id: "SET-005", title: "Workspaces", href: "/settings/workspaces", priority: "Should" },
      { id: "SET-006", title: "Roles", href: "/admin/roles", priority: "Should" },
      { id: "SET-007", title: "ABAC builder", href: "/admin/abac", priority: "Phase 2" },
      { id: "SET-008", title: "Data retention", href: "/admin/data-retention", priority: "Could" },
    ],
  },
  {
    label: "Errors",
    items: [
      {
        id: "ERR-001",
        title: "401 Auth required",
        href: "/error/authentication-required",
        priority: "MVP",
      },
      { id: "ERR-002", title: "403 Forbidden", href: "/error/forbidden", priority: "MVP" },
      {
        id: "ERR-003",
        title: "404 Patient not found",
        href: "/error/patient-not-found",
        priority: "MVP",
      },
      {
        id: "ERR-004",
        title: "422 Insufficient evidence",
        href: "/error/insufficient-evidence",
        priority: "MVP",
      },
      { id: "ERR-005", title: "422 OCR failed", href: "/error/ocr-failed", priority: "MVP" },
      { id: "ERR-006", title: "429 Rate limit", href: "/error/rate-limit", priority: "Should" },
      { id: "ERR-007", title: "503 LLM offline", href: "/error/llm-offline", priority: "MVP" },
    ],
  },
];

const priorityTone: Record<Item["priority"], string> = {
  MVP: "bg-primary/10 text-primary",
  Should: "bg-secondary/10 text-secondary",
  Could: "bg-info/10 text-info",
  "Phase 2": "bg-ai/10 text-ai",
};

function ScreensIndex() {
  const total = groups.reduce((n, g) => n + g.items.length, 0);
  return (
    <AppShell>
      <PageHeader
        title="Screen index"
        description={`Browse all ${total} screens in the prototype.`}
        chips={
          <>
            <Badge variant="secondary">{total} screens</Badge>
            <Badge variant="secondary" className="bg-primary/10 text-primary">
              MVP · 50
            </Badge>
            <Badge variant="secondary" className="bg-secondary/10 text-secondary">
              Should · 28
            </Badge>
            <Badge variant="secondary" className="bg-info/10 text-info">
              Could · 9
            </Badge>
            <Badge variant="secondary" className="bg-ai/10 text-ai">
              Phase 2 · 8
            </Badge>
          </>
        }
      />
      <div className="grid gap-4 lg:grid-cols-2">
        {groups.map((g) => (
          <Card key={g.label} className="overflow-hidden p-0">
            <div className="border-b bg-muted/40 px-4 py-2.5 text-sm font-semibold">{g.label}</div>
            <ul className="divide-y">
              {g.items.map((it) => (
                <li key={it.id}>
                  <a
                    href={it.href}
                    className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm hover:bg-accent"
                  >
                    <span className="flex items-center gap-3 min-w-0">
                      <span className="font-mono text-[10px] text-muted-foreground">{it.id}</span>
                      <span className="truncate font-medium">{it.title}</span>
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${priorityTone[it.priority]}`}
                    >
                      {it.priority}
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
