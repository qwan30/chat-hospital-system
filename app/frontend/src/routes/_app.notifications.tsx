import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelative } from "@/lib/format";
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
  {
    id: "n-007",
    kind: "ai",
    title: "High Risk Clinical Alert",
    body: "CDSS detected severe Bleeding Risk due to new Aspirin prescription. Cross-referenced with patient history.",
    ts: "2026-07-12T02:15:00Z",
    read: false,
    href: "/patients/11111111-1111-1111-1111-111111111111",
  },
];
import { KeyRound, ScanText, RotateCw, Sparkles, Cog } from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/_app/notifications")({
  head: () => ({ meta: [{ title: "Notifications — HMS AI Copilot" }] }),
  component: NotificationsPage,
});

const iconFor: Record<string, React.ComponentType<{ className?: string }>> = {
  access: KeyRound,
  ocr: ScanText,
  sync: RotateCw,
  ai: Sparkles,
  system: Cog,
};
const toneFor: Record<string, string> = {
  access: "bg-primary/10 text-primary",
  ocr: "bg-secondary/10 text-secondary",
  sync: "bg-warning/10 text-warning",
  ai: "bg-ai/10 text-ai",
  system: "bg-muted text-muted-foreground",
};

function NotificationsPage() {
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const list = filter === "unread" ? notifications.filter((n) => !n.read) : notifications;
  return (
    <AppShell>
      <PageHeader
        title="Notifications"
        description="Access requests, OCR jobs, sync events, and AI safety signals."
        actions={
          <Button variant="outline" size="sm">
            Mark all as read
          </Button>
        }
        chips={
          <>
            <Badge variant="secondary">{notifications.length} total</Badge>
            <Badge variant="secondary" className="bg-destructive/10 text-destructive">
              {notifications.filter((n) => !n.read).length} unread
            </Badge>
          </>
        }
      />
      <div className="mb-3 flex gap-2">
        <Button
          size="sm"
          variant={filter === "all" ? "default" : "outline"}
          onClick={() => setFilter("all")}
        >
          All
        </Button>
        <Button
          size="sm"
          variant={filter === "unread" ? "default" : "outline"}
          onClick={() => setFilter("unread")}
        >
          Unread
        </Button>
      </div>
      <Card className="divide-y p-0">
        {list.map((n) => {
          const Icon = iconFor[n.kind];
          return (
            <div
              key={n.id}
              className={`flex items-start gap-3 p-4 ${!n.read ? "bg-primary/5" : ""}`}
            >
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${toneFor[n.kind]}`}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <div className="text-sm font-semibold">{n.title}</div>
                  {!n.read ? <span className="h-1.5 w-1.5 rounded-full bg-primary" /> : null}
                </div>
                <div className="mt-0.5 text-sm text-muted-foreground">{n.body}</div>
                <div className="mt-1 text-xs text-muted-foreground">{formatRelative(n.ts)}</div>
              </div>
              {n.href ? (
                <Link
                  to={n.href as any}
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Open →
                </Link>
              ) : null}
            </div>
          );
        })}
      </Card>
    </AppShell>
  );
}
