import { CircleSlash, FileText, LockKeyhole, PanelRightOpen, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { EvidenceAvailability } from "@/lib/chat-assistant";
import { sampleEvidenceSources } from "@/lib/chat-assistant";

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

export function EvidencePanel() {
  return (
    <aside className="order-3 min-h-[360px] min-w-0 border-t border-white/10 bg-[#111214] lg:min-h-dvh lg:border-l lg:border-t-0">
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase text-[#8a8f98]">Evidence</p>
          <h2 className="truncate text-base font-semibold text-white">Source Panel</h2>
        </div>
        <Button size="icon" variant="ghost" aria-label="Toggle evidence panel">
          <PanelRightOpen className="size-4" />
        </Button>
      </div>

      <div className="space-y-3 p-4">
        {sampleEvidenceSources.map((item) => {
          const style = evidenceStyles[item.availability];
          const Icon = style.icon;

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
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#8a8f98]">
              {item.page ? <span>Page {item.page}</span> : null}
              {item.score !== null ? <span>Score {item.score.toFixed(2)}</span> : null}
              <span>{item.provenance.visibleLabel}</span>
            </div>
          </article>
          );
        })}

        <article className="rounded-md border border-[#f87171]/30 bg-[#f87171]/10 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-[#fecaca]">
            <ShieldAlert className="size-4" />
            Permission boundary
          </div>
          <p className="text-sm leading-5 text-[#f5b4b4]">
            The panel can show general sources now. Patient-linked evidence remains unavailable until permission
            validation is explicit.
          </p>
        </article>
      </div>
    </aside>
  );
}
