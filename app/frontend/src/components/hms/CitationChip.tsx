import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export interface CitationEvidenceRef {
  id?: string;
  document_id?: string;
  sourceId?: string;
  n?: number;
  [key: string]: unknown;
}

export interface CitationChipProps {
  n?: number;
  sourceId?: string;
  evidence?: CitationEvidenceRef;
  className?: string;
}

export function CitationChip({ n, sourceId, evidence, className }: CitationChipProps) {
  const finalN = n ?? evidence?.n ?? 1;
  const finalSourceId =
    sourceId ?? evidence?.sourceId ?? evidence?.document_id ?? evidence?.id ?? "";
  return (
    <Link
      to="/documents/$documentId"
      params={{ documentId: finalSourceId }}
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-citation/30 bg-citation/10 px-1 align-middle font-mono text-[10px] font-semibold text-citation transition hover:bg-citation/20",
        className,
      )}
    >
      [{finalN}]
    </Link>
  );
}
