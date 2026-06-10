import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles, AlertTriangle } from "lucide-react";

interface CitationMark {
  id: number;
  documentTitle: string;
  page: number;
}

interface AISummaryCardProps {
  sections: { title: string; content: string; citations?: number[] }[];
  confidence: "high" | "medium" | "low";
  citations?: CitationMark[];
  loading?: boolean;
  onCitationClick?: (citationId: number) => void;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-success-50 text-success-600 border-success-100",
  medium: "bg-warning-50 text-warning-500 border-warning-100",
  low: "bg-danger-50 text-danger-600 border-danger-100",
};

export function AISummaryCard({
  sections,
  confidence,
  citations,
  loading,
  onCitationClick,
}: AISummaryCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-5 space-y-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary-500" />
            <h3 className="text-h4 text-text-strong">AI-Generated Summary</h3>
          </div>
          <Badge variant="outline" className={CONFIDENCE_STYLES[confidence]}>
            {confidence === "high" ? "High Confidence" : confidence === "medium" ? "Medium Confidence" : "Low Confidence"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {sections.map((section, i) => (
          <div key={i}>
            <h4 className="text-[14px] font-semibold text-text-default mb-1.5">{section.title}</h4>
            <p className="text-body text-text-default leading-relaxed">
              {renderContentWithCitations(section.content, section.citations, citations, onCitationClick)}
            </p>
          </div>
        ))}
        {confidence === "low" && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100">
            <AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0 mt-0.5" />
            <p className="text-[12px] text-warning-700">
              This summary has low confidence. Please verify all information against the source documents before making clinical decisions.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function renderContentWithCitations(
  text: string,
  citationIds: number[] | undefined,
  citations: CitationMark[] | undefined,
  onCitationClick: ((id: number) => void) | undefined
): React.ReactNode {
  if (!citationIds || !citationIds.length || !citations || !citations.length) return text;

  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const id = parseInt(match[1]);
      return (
        <button
          key={i}
          onClick={() => onCitationClick && onCitationClick(id)}
          className="inline-flex items-center px-1 text-[11px] font-semibold text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors"
          title={citations.find((c) => c.id === id)?.documentTitle}
        >
          [{id}]
        </button>
      );
    }
    return <span key={i}>{part}</span>;
  });
}
