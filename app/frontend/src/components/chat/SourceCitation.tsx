import { CircleSlash, FileText, LockKeyhole } from "lucide-react";
import type { EvidenceAvailability, SourceCitation as SourceCitationModel } from "@/lib/chat-assistant";

const citationStyles: Record<
  EvidenceAvailability,
  {
    icon: typeof FileText;
    className: string;
  }
> = {
  available: {
    icon: FileText,
    className: "border-[#5e6ad2]/40 bg-[#5e6ad2]/10 text-[#cfd3ff] hover:bg-[#5e6ad2]/20",
  },
  "permission-gated": {
    icon: LockKeyhole,
    className: "border-[#fbbf24]/40 bg-[#fbbf24]/10 text-[#fde68a] hover:bg-[#fbbf24]/20",
  },
  unavailable: {
    icon: CircleSlash,
    className: "border-white/10 bg-white/[0.03] text-[#a3a7ad] hover:bg-white/[0.06]",
  },
  "no-evidence": {
    icon: CircleSlash,
    className: "border-[#f87171]/30 bg-[#f87171]/10 text-[#fecaca] hover:bg-[#f87171]/20",
  },
};

export function SourceCitation({ citation }: { citation: SourceCitationModel }) {
  const style = citationStyles[citation.availability];
  const Icon = style.icon;

  return (
    <a
      className={`inline-flex min-h-8 items-center rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${style.className}`}
      href={`#${citation.evidenceSourceId}`}
      aria-label={`Open source: ${citation.label}. ${citation.provenance.visibleLabel}.`}
    >
      <Icon className="mr-1.5 size-3.5 shrink-0" />
      <span className="truncate">{citation.label}</span>
    </a>
  );
}
