import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Sparkles, UserCheck, type LucideIcon, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getGlobalTimeline, TimelineEvent } from "@/lib/api/timeline";
import { format } from "date-fns";

export const Route = createFileRoute("/_app/timeline/")({
  head: () => ({
    meta: [{ title: "Timeline — HMS AI Copilot" }],
  }),
  component: TimelinePage,
});

type Tone = "primary" | "ai" | "warning" | "secondary" | "destructive" | "citation";

const toneColor: Record<Tone, string> = {
  primary: "bg-primary/10 text-primary",
  ai: "bg-ai/10 text-ai",
  warning: "bg-warning/10 text-warning",
  secondary: "bg-secondary/10 text-secondary",
  destructive: "bg-destructive/10 text-destructive",
  citation: "bg-citation/10 text-citation",
};

const getEventIconAndTone = (type: TimelineEvent["type"]): { icon: LucideIcon; tone: Tone } => {
  switch (type) {
    case "chat":
      return { icon: Sparkles, tone: "ai" };
    case "document":
      return { icon: FileText, tone: "primary" };
    case "audit":
      return { icon: UserCheck, tone: "secondary" };
    default:
      return { icon: FileText, tone: "primary" };
  }
};

function TimelinePage() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["global-timeline"],
    queryFn: () => getGlobalTimeline(),
  });

  return (
    <AppShell>
      <PageHeader
        title="Timeline"
        description="Unified clinical activity across your service line."
        chips={<Badge variant="secondary">Global Activity Feed</Badge>}
      />
      <Card className="p-6">
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="text-center text-destructive py-8">Failed to load timeline events.</div>
        ) : !data || data.events.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">No events found.</div>
        ) : (
          <ol className="relative space-y-6 border-l border-border pl-6">
            {data.events.map((e, i) => {
              const { icon: Icon, tone } = getEventIconAndTone(e.type);
              return (
                <li
                  key={e.event_id}
                  className="relative cursor-pointer hover:bg-muted/30 p-2 rounded-lg transition-colors"
                  onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
                >
                  <span
                    className={`absolute -left-[34px] top-3 flex h-7 w-7 items-center justify-center rounded-full border-2 border-background ${toneColor[tone]}`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                  </span>
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-xs text-muted-foreground">
                      {format(new Date(e.timestamp), "HH:mm")}
                    </span>
                    <h3 className="text-sm font-semibold">{e.title}</h3>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{e.body}</p>
                  {expandedIndex === i && (
                    <div className="mt-2 text-xs border-t pt-2 space-y-1 text-muted-foreground">
                      <div>
                        <strong>Event ID:</strong> {e.event_id}
                      </div>
                      <div>
                        <strong>Type:</strong> {e.type}
                      </div>
                      <div>
                        <strong>Date:</strong>{" "}
                        {format(new Date(e.timestamp), "MMM d, yyyy HH:mm:ss")}
                      </div>
                      {e.patient_id && (
                        <Link
                          to="/patients/$patientId"
                          params={{ patientId: e.patient_id }}
                          className="inline-block mt-1 font-semibold text-primary hover:underline"
                          onClick={(ev) => ev.stopPropagation()}
                        >
                          View Patient →
                        </Link>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </Card>
    </AppShell>
  );
}
