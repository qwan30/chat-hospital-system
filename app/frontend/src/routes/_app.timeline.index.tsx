import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/hms/PageHeader";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  FileText,
  Heart,
  Pill,
  Sparkles,
  Stethoscope,
  UserCheck,
  type LucideIcon,
} from "lucide-react";

export const Route = createFileRoute("/_app/timeline/")({
  head: () => ({
    meta: [{ title: "Timeline — HMS AI Copilot" }],
  }),
  component: TimelinePage,
});

interface Event {
  ts: string;
  title: string;
  body: string;
  icon: LucideIcon;
  tone: "primary" | "ai" | "warning" | "secondary" | "destructive" | "citation";
}

const events: Event[] = [
  {
    ts: "09:14",
    title: "AI consult: anticoagulation review",
    body: "Dr. Chen asked the copilot to evaluate Eleanor Vance's apixaban regimen. 4 citations returned.",
    icon: Sparkles,
    tone: "ai",
  },
  {
    ts: "08:42",
    title: "Echocardiogram indexed",
    body: "ECHO-48201 added to the knowledge base. LVEF 52%, no thrombus.",
    icon: FileText,
    tone: "primary",
  },
  {
    ts: "08:01",
    title: "Vitals alert: BP 162/98",
    body: "Raman, P. flagged on watch list. Notified Cardiology · 4N.",
    icon: Heart,
    tone: "destructive",
  },
  {
    ts: "07:30",
    title: "Medication updated",
    body: "Apixaban 5 mg BID renewed for Vance, E.",
    icon: Pill,
    tone: "secondary",
  },
  {
    ts: "06:48",
    title: "Sepsis bundle protocol uploaded",
    body: "Dr. Liu uploaded Sepsis-Bundle-2026.docx — currently processing.",
    icon: FileText,
    tone: "primary",
  },
  {
    ts: "06:30",
    title: "Care team huddle",
    body: "Cardiology 4N morning sign-out. 12 patients reviewed.",
    icon: Stethoscope,
    tone: "citation",
  },
  {
    ts: "06:14",
    title: "Access granted",
    body: "Dr. Chen granted view access to Vance, E. for clinical consult.",
    icon: UserCheck,
    tone: "secondary",
  },
  {
    ts: "05:55",
    title: "OCR completed",
    body: "Scanned-Consult-Müller.jpg → 2 pages extracted, queued for embedding.",
    icon: Activity,
    tone: "warning",
  },
];

const toneColor: Record<Event["tone"], string> = {
  primary: "bg-primary/10 text-primary",
  ai: "bg-ai/10 text-ai",
  warning: "bg-warning/10 text-warning",
  secondary: "bg-secondary/10 text-secondary",
  destructive: "bg-destructive/10 text-destructive",
  citation: "bg-citation/10 text-citation",
};

function TimelinePage() {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  return (
    <AppShell>
      <PageHeader
        title="Timeline"
        description="Unified clinical activity across your service line."
        chips={<Badge variant="secondary">Today, Jun 12</Badge>}
      />
      <Card className="p-6">
        <ol className="relative space-y-6 border-l border-border pl-6">
          {events.map((e, i) => (
            <li
              key={i}
              className="relative cursor-pointer hover:bg-muted/30 p-2 rounded-lg transition-colors"
              onClick={() => setExpandedIndex(expandedIndex === i ? null : i)}
            >
              <span
                className={`absolute -left-[34px] top-3 flex h-7 w-7 items-center justify-center rounded-full border-2 border-background ${toneColor[e.tone]}`}
              >
                <e.icon className="h-3.5 w-3.5" />
              </span>
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-xs text-muted-foreground">{e.ts}</span>
                <h3 className="text-sm font-semibold">{e.title}</h3>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{e.body}</p>
              {expandedIndex === i && (
                <div className="mt-2 text-xs border-t pt-2 space-y-1 text-muted-foreground">
                  <div>
                    <strong>Event ID:</strong> ev-00{i + 1}
                  </div>
                  <div>
                    <strong>Outcome:</strong> success
                  </div>
                  <div>
                    <strong>Trace ID:</strong> tr-99{i + 1}
                  </div>
                  {e.body.includes("Vance, E.") || e.body.includes("Eleanor Vance") ? (
                    <Link
                      to="/patients/$patientId"
                      params={{ patientId: "p-001" }}
                      className="inline-block mt-1 font-semibold text-primary hover:underline"
                      onClick={(ev) => ev.stopPropagation()}
                    >
                      View Patient Eleanor Vance →
                    </Link>
                  ) : e.body.includes("Raman, P.") ? (
                    <Link
                      to="/patients/$patientId"
                      params={{ patientId: "p-004" }}
                      className="inline-block mt-1 font-semibold text-primary hover:underline"
                      onClick={(ev) => ev.stopPropagation()}
                    >
                      View Patient Priya Raman →
                    </Link>
                  ) : null}
                </div>
              )}
            </li>
          ))}
        </ol>
      </Card>
    </AppShell>
  );
}
