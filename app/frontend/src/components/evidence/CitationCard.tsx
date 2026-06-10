import { FileText, ChevronRight } from "lucide-react";

interface CitationCardProps {
  id: number;
  documentTitle: string;
  page: number;
  snippet: string;
  confidence: number;
  onClick?: () => void;
}

export function CitationCard({ id, documentTitle, page, snippet, confidence, onClick }: CitationCardProps) {
  const confidenceColor = confidence >= 0.8 ? "text-success-600 bg-success-50" : confidence >= 0.5 ? "text-warning-500 bg-warning-50" : "text-danger-600 bg-danger-50";

  return (
    <button onClick={onClick} className="w-full text-left p-3 bg-bg-surface-tint rounded-lg border border-border-subtle hover:border-primary-200 hover:shadow-card transition-all group">
      <div className="flex items-start justify-between mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-3.5 h-3.5 text-text-subtle flex-shrink-0" />
          <span className="text-[13px] font-medium text-text-default truncate">{documentTitle}</span>
        </div>
        <span className={"text-[10px] font-semibold px-1.5 py-0.5 rounded flex-shrink-0 ml-2 " + confidenceColor}>{Math.round(confidence * 100)}%</span>
      </div>
      <p className="text-[12px] text-text-muted line-clamp-2 mb-1">{snippet}</p>
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-text-subtle">Page {page} · Source #{id}</span>
        <ChevronRight className="w-3.5 h-3.5 text-text-subtle group-hover:text-primary-500 transition-colors" />
      </div>
    </button>
  );
}
