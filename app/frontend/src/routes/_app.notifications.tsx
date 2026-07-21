import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { formatRelative } from "@/lib/format";
import { useQuery } from "@tanstack/react-query";
import { listAccessRequests } from "@/lib/api/access-requests";
export interface AppNotification {
  id: string;
  kind: "access" | "ocr" | "sync" | "ai" | "system";
  title: string;
  body: string;
  ts: string;
  read: boolean;
  href?: string;
  /** If set, resolve href from the nth real access request returned by the API */
  accessRequestIndex?: number;
}

// Static notification list — access-request hrefs are resolved dynamically from the API
export const staticNotifications: AppNotification[] = [
  {
    id: "n-001",
    kind: "access",
    title: "Access request approved",
    body: "Amelia Brooks (MRN-48994) — granted by Admin J. Kim",
    ts: "2026-06-12T13:24:00Z",
    read: false,
    // href resolved at runtime from real access-request IDs (index 1)
    href: undefined,
    accessRequestIndex: 1,
  },
  {
    id: "n-002",
    kind: "ocr",
    title: "OCR completed",
    body: "Echo-Report-2026-06-11.pdf indexed (12 chunks)",
    ts: "2026-06-12T13:02:00Z",
    read: false,
    href: "/documents",
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
    // href resolved at runtime from real access-request IDs (index 0)
    href: undefined,
    accessRequestIndex: 0,
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
  const [items, setItems] = useState<AppNotification[]>(staticNotifications);

  // Fetch real access-request IDs from the backend to resolve notification hrefs
  const { data: accessRequests, isLoading: arLoading } = useQuery({
    queryKey: ["access-requests"],
    queryFn: listAccessRequests,
    staleTime: 60_000,
  });

  // Build resolved notifications: replace accessRequestIndex with a real href
  const resolvedItems = items.map((n) => {
    if (n.accessRequestIndex !== undefined && accessRequests) {
      const ar = accessRequests[n.accessRequestIndex];
      return ar && ar.id
        ? { ...n, href: `/access-requests/${ar.id}` }
        : { ...n, href: "/access-requests" };
    }
    return n;
  });

  const markAllAsRead = () => {
    setItems((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const list = filter === "unread" ? resolvedItems.filter((n) => !n.read) : resolvedItems;
  return (
    <AppShell>
      <PageHeader
        title="Notifications"
        description="Access requests, OCR jobs, sync events, and AI safety signals."
        actions={
          <Button variant="outline" size="sm" onClick={markAllAsRead}>
            Mark all as read
          </Button>
        }
        chips={
          <>
            <Badge variant="secondary">{items.length} total</Badge>
            <Badge variant="secondary" className="bg-destructive/10 text-destructive">
              {items.filter((n) => !n.read).length} unread
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
                  className="shrink-0 text-xs font-semibold text-primary hover:underline"
                >
                  Open →
                </Link>
              ) : n.accessRequestIndex !== undefined && arLoading ? (
                <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground" />
              ) : null}
            </div>
          );
        })}
      </Card>
    </AppShell>
  );
}
