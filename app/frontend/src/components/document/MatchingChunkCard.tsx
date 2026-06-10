import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

export function MatchingChunkCard({ documentTitle, chunk, score }: { documentTitle: string; chunk: string; score: number }) {
  return (
    <div className="p-3 bg-bg-surface-tint rounded-lg border border-border-subtle hover:border-border-default transition-colors">
      <div className="flex items-center gap-2 mb-1"><FileText className="w-3 h-3 text-text-subtle" /><span className="text-[12px] font-medium text-text-default">{documentTitle}</span></div>
      <p className="text-[12px] text-text-muted line-clamp-2 mb-1">{chunk}</p>
      <Badge variant="outline" className={score >= 0.8 ? "bg-success-50 text-success-600" : score >= 0.5 ? "bg-warning-50 text-warning-500" : "bg-danger-50 text-danger-600"}>{Math.round(score * 100)}% match</Badge>
    </div>
  );
}
