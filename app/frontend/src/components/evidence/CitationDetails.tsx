import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

interface CitationDetailsProps {
  documentTitle: string;
  page: number;
  snippet: string;
  confidence: number;
  metadata?: Record<string, string>;
}

export function CitationDetails({ documentTitle, page, snippet, confidence, metadata }: CitationDetailsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2"><FileText className="w-4 h-4 text-text-subtle" /><h4 className="text-h4 text-text-strong">{documentTitle}</h4></div>
      <div className="flex items-center gap-2">
        <span className="text-[12px] text-text-muted">Page {page}</span>
        <Badge variant="outline" className={confidence >= 0.8 ? "bg-success-50 text-success-600" : "bg-warning-50 text-warning-500"}>{Math.round(confidence * 100)}% confidence</Badge>
      </div>
      <div className="p-3 bg-bg-surface-tint rounded-lg border border-border-subtle"><p className="text-[13px] text-text-muted leading-relaxed italic">{snippet}</p></div>
      {metadata && <div className="space-y-1.5">{Object.entries(metadata).map(([k, v]) => <div key={k} className="flex justify-between"><span className="text-[11px] text-text-subtle">{k}</span><span className="text-[12px] text-text-default">{v}</span></div>)}</div>}
    </div>
  );
}
