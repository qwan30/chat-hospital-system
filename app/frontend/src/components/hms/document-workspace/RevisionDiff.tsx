import { ScrollArea } from "@/components/ui/scroll-area";

export function RevisionDiff({
  originalText,
  correctedText,
}: {
  originalText: string;
  correctedText: string;
}) {
  return (
    <div className="flex flex-col md:flex-row gap-3 flex-1 h-full min-h-0">
      <div className="flex-1 flex flex-col border border-border/80 rounded-xl p-3.5 bg-muted/20 overflow-hidden shadow-inner min-h-0">
        <div className="flex items-center justify-between mb-2 select-none">
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Original OCR
          </span>
          <span className="text-[10px] text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">
            Baseline
          </span>
        </div>
        <ScrollArea className="flex-1 min-h-0">
          <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed text-foreground/90 p-1">
            {originalText || "No original text available"}
          </pre>
        </ScrollArea>
      </div>

      <div className="flex-1 flex flex-col border border-primary/20 rounded-xl p-3.5 bg-primary/5 overflow-hidden shadow-inner min-h-0">
        <div className="flex items-center justify-between mb-2 select-none">
          <span className="text-[11px] font-semibold text-primary uppercase tracking-wider">
            Corrected Text
          </span>
          <span className="text-[10px] text-primary bg-primary/10 px-1.5 py-0.5 rounded font-medium">
            Active Version
          </span>
        </div>
        <ScrollArea className="flex-1 min-h-0">
          <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed text-foreground p-1">
            {correctedText || "No corrected text available"}
          </pre>
        </ScrollArea>
      </div>
    </div>
  );
}
