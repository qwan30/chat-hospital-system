import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export interface CitationEvidenceRef {
  id?: string;
  document_id?: string;
  sourceId?: string;
  page?: number;
  n?: number;
  [key: string]: unknown;
}

export interface CitationChipProps {
  n?: number;
  sourceId?: string;
  page?: number;
  evidence?: CitationEvidenceRef;
  className?: string;
}

export function CitationChip({ n, sourceId, page, evidence, className }: CitationChipProps) {
  const finalN = n ?? evidence?.n ?? 1;
  const rawId = evidence?.document_id || sourceId || evidence?.id || "";
  const pageNum = page ?? (evidence?.page as number | undefined) ?? 1;

  // Filter out evidence indices (e.g. "E1", "E2"), pure numbers, or graph nodes ("pt") that are not valid document IDs
  const isValidDocId =
    typeof rawId === "string" &&
    rawId.length > 0 &&
    !/^E\d+$/i.test(rawId) &&
    !/^\d+$/.test(rawId) &&
    rawId !== "pt";

  if (!isValidDocId) {
    return (
      <span
        title={evidence ? `Citation [${finalN}]` : undefined}
        className={cn(
          "inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-citation/30 bg-citation/10 px-1 align-middle font-mono text-[10px] font-semibold text-citation",
          className,
        )}
      >
        [{finalN}]
      </span>
    );
  }

  return (
    <Link
      to="/documents/$documentId"
      params={{ documentId: rawId }}
      search={{ page: pageNum }}
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center rounded-md border border-citation/30 bg-citation/10 px-1 align-middle font-mono text-[10px] font-semibold text-citation transition hover:bg-citation/20",
        className,
      )}
    >
      [{finalN}]
    </Link>
  );
}
