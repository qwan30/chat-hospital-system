import { ScrollArea } from "@/components/ui/scroll-area";

export function RevisionDiff({
  originalText,
  correctedText,
}: {
  originalText: string;
  correctedText: string;
}) {
  return (
    <div className="flex flex-col md:flex-row gap-4 h-[300px]">
      <div className="flex-1 flex flex-col border rounded-md p-4 bg-muted/20 overflow-hidden">
        <h3 className="text-sm font-semibold mb-2 text-muted-foreground">Original Text</h3>
        <ScrollArea className="flex-1">
          <pre className="text-sm whitespace-pre-wrap font-sans">{originalText || "No original text available"}</pre>
        </ScrollArea>
      </div>
      <div className="flex-1 flex flex-col border rounded-md p-4 bg-muted/20 overflow-hidden">
        <h3 className="text-sm font-semibold mb-2 text-muted-foreground">Corrected Text</h3>
        <ScrollArea className="flex-1">
          <pre className="text-sm whitespace-pre-wrap font-sans">{correctedText || "No corrected text available"}</pre>
        </ScrollArea>
      </div>
    </div>
  );
}
