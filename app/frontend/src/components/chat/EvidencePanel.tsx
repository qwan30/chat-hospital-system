import { CheckCircle2, CircleDashed, CircleSlash, FileText, Globe2, LockKeyhole, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ConversationThread, EvidenceAvailability, EvidenceSource, PatientContext } from "@/lib/chat-assistant";

const evidenceStyles: Record<
  EvidenceAvailability,
  {
    label: string;
    icon: typeof FileText;
    className: string;
  }
> = {
  available: {
    label: "Available",
    icon: FileText,
    className: "border-white/10 bg-white/[0.03]",
  },
  "permission-gated": {
    label: "Gated",
    icon: LockKeyhole,
    className: "border-[#fbbf24]/30 bg-[#fbbf24]/10",
  },
  unavailable: {
    label: "Unavailable",
    icon: CircleSlash,
    className: "border-white/10 bg-white/[0.02]",
  },
  "no-evidence": {
    label: "No evidence",
    icon: CircleSlash,
    className: "border-[#f87171]/30 bg-[#f87171]/10",
  },
};

export function EvidencePanel({
  activeContext,
  activeThread,
  evidenceSources,
}: {
  activeContext: PatientContext | undefined;
  activeThread: ConversationThread | undefined;
  evidenceSources: EvidenceSource[];
}) {
  const boundary = permissionBoundaryFor(activeContext);
  const BoundaryIcon = boundary.icon;

  return (
    <aside className="order-3 min-h-[360px] min-w-0 border-t border-white/10 bg-[#111214] lg:min-h-dvh lg:border-l lg:border-t-0">
      <div className="flex h-16 items-center border-b border-white/10 px-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase text-[#8a8f98]">Evidence</p>
          <h2 className="truncate text-base font-semibold text-white">Source Panel</h2>
        </div>
      </div>

      <div className="space-y-3 p-4">
        {evidenceSources.length === 0 ? (
          <article className="rounded-md border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
              <CircleSlash className="size-4 text-[#8a8f98]" />
              No active thread evidence
            </div>
            <p className="text-sm leading-5 text-[#a3a7ad]">
              {activeThread
                ? `${activeThread.title} has no cited evidence yet.`
                : "Choose a conversation before inspecting evidence."}
            </p>
          </article>
        ) : null}

        {/* Low evidence quality warning */}
        {evidenceSources.length > 0 && evidenceSources.every((s) => (s.score ?? 0) < 0.55) ? (
          <div className="flex items-start gap-2.5 rounded-md border border-[#fbbf24]/30 bg-[#fbbf24]/10 p-3">
            <ShieldAlert className="mt-0.5 size-4 shrink-0 text-[#fbbf24]" />
            <div>
              <p className="text-xs font-medium text-[#fde68a]">Low Evidence Quality</p>
              <p className="mt-0.5 text-xs text-[#d4a574]">
                All retrieved evidence scores are below the medium threshold (0.55).
                The AI answer may be less reliable. Consider refining your query.
              </p>
            </div>
          </div>
        ) : null}

        {evidenceSources.map((item) => {
          const style = evidenceStyles[item.availability];
          const Icon = style.icon;
          const score = item.score ?? 0;
          const scoreColor = score >= 0.78 ? "#34d399" : score >= 0.55 ? "#fbbf24" : "#f87171";
          const scoreLabel = score >= 0.78 ? "High" : score >= 0.55 ? "Medium" : "Low";
          const scorePercent = Math.min(Math.max(score * 100, 0), 100);

          return (
          <article key={item.id} id={item.id} className={`scroll-mt-4 rounded-md border p-4 ${style.className}`}>
            <div className="mb-2 flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2 text-sm font-medium text-white">
                <Icon className="size-4 shrink-0 text-[#60a5fa]" />
                <span className="truncate">{item.title}</span>
              </div>
              <Badge className="shrink-0">{style.label}</Badge>
            </div>
            <p className="text-sm leading-5 text-[#a3a7ad]">{item.excerpt}</p>

            {/* Relevance score bar */}
            {item.score !== null && (
              <div className="mt-3">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs text-[#8a8f98]">Relevance</span>
                  <span className="text-xs font-medium" style={{ color: scoreColor }}>
                    {scoreLabel} ({(score * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${scorePercent}%`,
                      backgroundColor: scoreColor,
                    }}
                  />
                </div>
              </div>
            )}

            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#8a8f98]">
              {item.page ? <span>Page {item.page}</span> : null}
              <span>{item.provenance.visibleLabel}</span>
              {typeof item.metadata.source_family === "string" ? <span>{item.metadata.source_family}</span> : null}
              {typeof item.metadata.source_record_id === "string" ? (
                <span>Source {item.metadata.source_record_id.slice(0, 8)}</span>
              ) : null}
            </div>
          </article>
          );
        })}

        <article className={`rounded-md border p-4 ${boundary.className}`}>
          <div className="mb-2 flex items-center gap-2 text-sm font-medium">
            <BoundaryIcon className="size-4" />
            {boundary.label}
          </div>
          <p className="text-sm leading-5">{boundary.detail}</p>
        </article>
      </div>
    </aside>
  );
}

function permissionBoundaryFor(context: PatientContext | undefined): {
  icon: typeof FileText;
  label: string;
  detail: string;
  className: string;
} {
  if (!context) {
    return {
      icon: CircleSlash,
      label: "No active scope",
      detail: "Choose a conversation before inspecting permission-scoped evidence.",
      className: "border-white/10 bg-white/[0.02] text-[#a3a7ad]",
    };
  }

  if (context.permissionState === "not-required") {
    return {
      icon: Globe2,
      label: "General evidence allowed",
      detail: `Active scope: ${context.displayLabel}. General hospital knowledge uses approved non-PHI sources without patient-linked evidence.`,
      className: "border-[#60a5fa]/30 bg-[#60a5fa]/10 text-[#bfdbfe]",
    };
  }

  if (context.permissionState === "allowed") {
    return {
      icon: CheckCircle2,
      label: "Patient evidence allowed",
      detail: `Active scope: ${context.displayLabel}. Backend permission is allowed, so patient-linked evidence may be shown when citations are returned.`,
      className: "border-[#34d399]/30 bg-[#34d399]/10 text-[#bbf7d0]",
    };
  }

  if (context.permissionState === "pending") {
    return {
      icon: CircleDashed,
      label: "Permission pending",
      detail: `Active scope: ${context.displayLabel}. Patient-linked evidence remains unavailable until backend permission validation completes.`,
      className: "border-[#fbbf24]/30 bg-[#fbbf24]/10 text-[#fde68a]",
    };
  }

  return {
    icon: ShieldAlert,
    label: "Permission denied",
    detail: `Active scope: ${context.displayLabel}. Patient-linked evidence and citations remain hidden for this context.`,
    className: "border-[#f87171]/30 bg-[#f87171]/10 text-[#fecaca]",
  };
}
