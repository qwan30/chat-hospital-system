import { ScrollArea } from "@/components/ui/scroll-area";

export function RevisionDiff({
  originalText,
  correctedText,
}: {
  originalText: string;
  correctedText: string;
}) {
  return (
    <div className="flex flex-col md:flex-row gap-4 flex-1 h-full min-h-[600px] lg:min-h-[750px]">
      <div className="flex-1 flex flex-col border rounded-xl p-4 bg-muted/20 overflow-hidden shadow-inner">
        <h3 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wider">Original Text</h3>
        <ScrollArea className="flex-1">
          <pre className="text-xs sm:text-sm whitespace-pre-wrap font-mono leading-relaxed text-foreground">
            {originalText || "No original text available"}
          </pre>
        </ScrollArea>
      </div>
      <div className="flex-1 flex flex-col border rounded-xl p-4 bg-muted/20 overflow-hidden shadow-inner">
        <h3 className="text-xs font-semibold mb-2 text-muted-foreground uppercase tracking-wider">Corrected Text</h3>
        <ScrollArea className="flex-1">
          <pre className="text-xs sm:text-sm whitespace-pre-wrap font-mono leading-relaxed text-foreground">
            {correctedText || "No corrected text available"}
          </pre>
        </ScrollArea>
      </div>
    </div>
  );
}
