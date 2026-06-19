export interface AppNotification {
  id: string;
  kind: "access" | "ocr" | "sync" | "ai" | "system";
  title: string;
  body: string;
  ts: string;
  read: boolean;
  href?: string;
}

export const notifications: AppNotification[] = [
  {
    id: "n-001",
    kind: "access",
    title: "Access request approved",
    body: "Amelia Brooks (MRN-48994) — granted by Admin J. Kim",
    ts: "2026-06-12T13:24:00Z",
    read: false,
    href: "/access-requests/ar-002",
  },
  {
    id: "n-002",
    kind: "ocr",
    title: "OCR completed",
    body: "Echo-Report-2026-06-11.pdf indexed (12 chunks)",
    ts: "2026-06-12T13:02:00Z",
    read: false,
    href: "/documents/d-04",
  },
  {
    id: "n-003",
    kind: "sync",
    title: "HMS sync degraded",
    body: "Last sync 18 min ago. Target SLA 15 min.",
    ts: "2026-06-12T12:55:00Z",
    read: false,
    href: "/integrations/hms",
  },
  {
    id: "n-004",
    kind: "ai",
    title: "Safe refusal recorded",
    body: "Insufficient evidence to answer GDMT titration query.",
    ts: "2026-06-12T11:40:00Z",
    read: true,
    href: "/audit",
  },
  {
    id: "n-005",
    kind: "access",
    title: "Access request pending",
    body: "Yuki Tanaka (MRN-48577) — your justification under review",
    ts: "2026-06-12T10:20:00Z",
    read: true,
    href: "/access-requests/ar-001",
  },
  {
    id: "n-006",
    kind: "system",
    title: "Vector index rebuilt",
    body: "Nightly index refresh completed in 4m 12s.",
    ts: "2026-06-12T03:14:00Z",
    read: true,
    href: "/integrations/vector-index",
  },
];
