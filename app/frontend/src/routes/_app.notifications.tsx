import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { notifications } from "@/data/notifications";
import { formatRelative } from "@/lib/format";
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
                <a href={n.href} className="text-xs font-semibold text-primary hover:underline">
                  Open →
                </a>
              ) : null}
            </div>
          );
        })}
      </Card>
    </AppShell>
  );
}
