import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, AlertTriangle } from "lucide-react";

interface AssistantCardProps {
  content: string;
  sections?: { title: string; content: string; citations?: number[] }[];
  confidence?: "high" | "medium" | "low";
  citations?: { id: number; title: string }[];
  timestamp?: string;
  onCitationClick?: (citationId: number) => void;
}

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-success-50 text-success-600",
  medium: "bg-warning-50 text-warning-500",
  low: "bg-danger-50 text-danger-600",
};

export function AssistantCard({ content, sections, confidence = "high", citations, timestamp, onCitationClick }: AssistantCardProps) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0 mt-1">
        <Sparkles className="w-4 h-4 text-primary-600" />
      </div>
      <div className="flex-1 space-y-3 max-w-[75%]">
        <Card>
          <CardContent className="p-4 space-y-4">
            {sections ? sections.map((s, i) => (
              <div key={i}>
                <h4 className="text-[14px] font-semibold text-text-default mb-1">{s.title}</h4>
                <p className="text-[14px] text-text-default leading-relaxed">
                  {s.content}
                  {s.citations?.map((cid) => (
                    <button key={cid} onClick={() => onCitationClick?.(cid)} className="inline-flex items-center px-1 ml-0.5 text-[11px] font-semibold text-primary-600 bg-primary-50 rounded hover:bg-primary-100">
                      [{cid}]
                    </button>
                  ))}
                </p>
              </div>
            )) : (
              <p className="text-[14px] text-text-default leading-relaxed">{content}</p>
            )}
            <div className="flex items-center justify-between pt-2 border-t border-border-subtle">
              <Badge variant="outline" className={CONFIDENCE_STYLES[confidence] + " text-[10px]"}>
                {confidence === "high" ? "High confidence" : confidence === "medium" ? "Medium confidence" : "Low confidence"}
              </Badge>
              {timestamp && <span className="text-[11px] text-text-subtle">{timestamp}</span>}
            </div>
          </CardContent>
        </Card>
        {confidence === "low" && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100">
            <AlertTriangle className="w-4 h-4 text-warning-500 flex-shrink-0 mt-0.5" />
            <p className="text-[12px] text-warning-700">Low confidence. Verify information against source documents.</p>
          </div>
        )}
      </div>
    </div>
  );
}
