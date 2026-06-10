import { Badge } from "@/components/ui/badge";

export function ExtractedTextPane({ text, confidence = 0.92 }: { text: string; confidence?: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between"><h4 className="text-h4 text-text-strong">Extracted Text</h4><Badge variant="outline" className={confidence >= 0.9 ? "bg-success-50 text-success-600" : "bg-warning-50 text-warning-500"}>OCR: {Math.round(confidence * 100)}%</Badge></div>
      <div className="bg-bg-surface-tint rounded-xl border border-border-subtle p-4 h-[500px] overflow-y-auto"><p className="text-[13px] text-text-default leading-relaxed whitespace-pre-wrap">{text}</p></div>
    </div>
  );
}
