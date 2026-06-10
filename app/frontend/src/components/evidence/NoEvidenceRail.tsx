import { SearchX } from "lucide-react";

export function NoEvidenceRail() {
  return (
    <div className="flex flex-col items-center py-6 px-4 text-center">
      <SearchX className="w-8 h-8 text-text-subtle mb-2" />
      <p className="text-[13px] font-medium text-text-muted mb-1">No evidence found</p>
      <p className="text-[11px] text-text-subtle">No supporting documents were retrieved for this query.</p>
    </div>
  );
}
