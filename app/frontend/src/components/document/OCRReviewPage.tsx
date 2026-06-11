import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileText, AlertTriangle, CheckCircle } from "lucide-react";
import { toast } from "sonner";

interface OCRReviewProps { documentTitle: string; ocrConfidence: number; sections: { text: string; confidence: number }[]; onConfirm?: () => void; }

export function OCRReviewPage({ documentTitle, ocrConfidence, sections, onConfirm }: OCRReviewProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><FileText className="w-5 h-5 text-text-subtle" /><h2 className="text-h3 text-text-strong">{documentTitle}</h2><Badge variant="outline" className={ocrConfidence >= 0.9 ? "bg-success-50 text-success-600" : "bg-warning-50 text-warning-500"}>OCR: {Math.round(ocrConfidence * 100)}%</Badge></div>
        <Button className="gap-2" onClick={() => { toast("Indexing started", { description: "Document has been queued for indexing." }); onConfirm?.(); }}><CheckCircle className="w-4 h-4" />Confirm & Index</Button>
      </div>
      {sections.some((s) => s.confidence < 0.8) && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-warning-50 border border-warning-100"><AlertTriangle className="w-4 h-4 text-warning-500" /><p className="text-[13px] text-warning-700">{sections.filter((s) => s.confidence < 0.8).length} sections have low OCR confidence. Please review highlighted text.</p></div>
      )}
      <div className="space-y-2">
        {sections.map((s, i) => (
          <div key={i} className={"p-3 rounded-lg border " + (s.confidence < 0.8 ? "bg-warning-50 border-warning-100" : "bg-bg-surface-tint border-border-subtle")}>
            <div className="flex items-center justify-between mb-1"><span className="text-[11px] text-text-subtle">Section {i + 1}</span><Badge variant="outline" className={s.confidence >= 0.8 ? "bg-success-50 text-success-600" : "bg-danger-50 text-danger-600"}>{Math.round(s.confidence * 100)}%</Badge></div>
            <p className="text-[13px] text-text-default leading-relaxed">{s.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
