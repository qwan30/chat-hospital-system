import { FileText, PanelRightOpen, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const evidenceItems = [
  {
    title: "Hospital policy manual",
    detail: "General knowledge source, page 12",
    status: "Available",
  },
  {
    title: "Patient-linked chart",
    detail: "Hidden until permission is allowed",
    status: "Gated",
  },
];

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
        {evidenceItems.map((item) => (
          <article key={item.title} className="rounded-md border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-2 flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2 text-sm font-medium text-white">
                <FileText className="size-4 shrink-0 text-[#60a5fa]" />
                <span className="truncate">{item.title}</span>
              </div>
              <Badge className="shrink-0">{item.status}</Badge>
            </div>
            <p className="text-sm leading-5 text-[#a3a7ad]">{item.detail}</p>
          </article>
        ))}

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
