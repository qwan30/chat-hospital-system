import { FileText } from "lucide-react";

export function ScannedPagePane({ pageNumber = 1, totalPages = 1 }: { pageNumber?: number; totalPages?: number }) {
  return (
    <div className="bg-bg-surface-tint rounded-xl border border-border-subtle h-[500px] flex items-center justify-center">
      <div className="text-center"><FileText className="w-16 h-16 text-text-subtle mx-auto mb-3" /><p className="text-[14px] text-text-muted">Scanned Document</p><p className="text-[12px] text-text-subtle">Page {pageNumber} of {totalPages}</p></div>
    </div>
  );
}
