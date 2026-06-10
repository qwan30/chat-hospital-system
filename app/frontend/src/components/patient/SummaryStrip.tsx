import { ContextChip } from "./ContextChip";

interface SummaryStripProps {
  fullName: string;
  mrn: string;
  extra?: string;
}

export function SummaryStrip({ fullName, mrn, extra }: SummaryStripProps) {
  return (
    <div className="flex items-center gap-3">
      <ContextChip fullName={fullName} mrn={mrn} size="sm" />
      {extra && (
        <span className="text-[12px] text-text-muted">{extra}</span>
      )}
    </div>
  );
}
