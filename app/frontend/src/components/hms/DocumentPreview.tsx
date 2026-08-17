import { useEffect, useState } from "react";
import { FileText, Loader2, Maximize2, Download } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { getDocumentBlob } from "@/lib/api/documents";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { SpreadsheetPreview } from "./SpreadsheetPreview";

export function DocumentPreview({
  documentId,
  mimeType,
  documentTitle,
  children,
}: {
  documentId: string;
  mimeType: string;
  documentTitle?: string;
  children?: React.ReactNode;
}) {
  const reduceMotion = useReducedMotion();
  const [blob, setBlob] = useState<Blob | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let currentUrl: string | null = null;
    let active = true;
    setBlob(null);
    setUrl(null);
    setFailed(false);
    getDocumentBlob(documentId)
      .then((fetchedBlob) => {
        if (!active) return;
        setBlob(fetchedBlob);
        currentUrl = URL.createObjectURL(fetchedBlob);
        setUrl(currentUrl);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [documentId]);

  const isSpreadsheet =
    mimeType.includes("csv") ||
    mimeType.includes("excel") ||
    mimeType.includes("spreadsheet") ||
    mimeType.includes("sheet") ||
    mimeType === "text/tab-separated-values" ||
    (documentTitle &&
      (documentTitle.toLowerCase().endsWith(".csv") ||
        documentTitle.toLowerCase().endsWith(".xlsx") ||
        documentTitle.toLowerCase().endsWith(".xls") ||
        documentTitle.toLowerCase().includes("sheet")));

  return (
    <AnimatePresence mode="wait" initial={false}>
      {failed ? (
        <motion.p
          key="unavailable"
          className="text-sm text-muted-foreground"
          {...fade(reduceMotion)}
        >
          Preview unavailable for this document.
        </motion.p>
      ) : !url || !blob ? (
        <motion.div
          key="loading"
          className="flex items-center justify-center gap-2 text-sm text-muted-foreground h-full"
          {...fade(reduceMotion)}
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading preview…
        </motion.div>
      ) : isSpreadsheet ? (
        <motion.div
          key="spreadsheet"
          className="relative w-full h-full flex-1 flex flex-col min-h-0 overflow-hidden"
          {...fade(reduceMotion)}
        >
          <SpreadsheetPreview blob={blob} downloadUrl={url} filename={documentTitle} />
          {children}
        </motion.div>
      ) : mimeType.startsWith("image/") ? (
        <motion.div
          key="image"
          className="relative group w-full h-full flex-1 flex flex-col min-h-0 overflow-hidden"
          {...fade(reduceMotion)}
        >
          <img
            src={url}
            alt="Document preview"
            className="w-full h-full flex-1 min-h-0 rounded-xl border object-contain bg-muted/10"
          />
          {children}
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="absolute top-2.5 right-2.5 h-7 w-7 rounded-lg bg-background/90 backdrop-blur-sm border shadow-sm z-10 text-muted-foreground hover:text-foreground"
                title="View fullscreen"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-[95vw] w-full max-h-[95vh] h-full p-2 flex flex-col border-none bg-background/95 backdrop-blur">
              <img src={url} alt="Fullscreen preview" className="w-full h-full object-contain" />
            </DialogContent>
          </Dialog>
        </motion.div>
      ) : mimeType === "application/pdf" ? (
        <motion.div
          key="pdf"
          className="relative group w-full h-full flex-1 flex flex-col min-h-0 overflow-hidden"
          {...fade(reduceMotion)}
        >
          <iframe
            title="Document preview"
            src={url}
            className="h-full w-full flex-1 min-h-0 rounded-xl border bg-background"
          />
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="absolute top-2.5 right-2.5 h-7 w-7 rounded-lg bg-background/90 backdrop-blur-sm border shadow-sm z-10 text-muted-foreground hover:text-foreground"
                title="View fullscreen"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-[95vw] w-full max-h-[95vh] h-[95vh] p-0 overflow-hidden border-none">
              <iframe src={url} className="w-full h-full" title="Fullscreen Document" />
            </DialogContent>
          </Dialog>
        </motion.div>
      ) : (
        <motion.div
          key="download-card"
          className="flex flex-col items-center justify-center gap-3 text-sm text-muted-foreground h-full p-8 text-center"
          {...fade(reduceMotion)}
        >
          <FileText className="h-10 w-10 text-muted-foreground/60" />
          <div>
            <p className="font-semibold text-foreground">{documentTitle || "Clinical Document"}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Binary format preview not available.
            </p>
          </div>
          <Button
            asChild
            size="sm"
            variant="outline"
            className="gap-1.5 h-8 text-xs rounded-lg mt-2"
          >
            <a href={url} download={documentTitle || "document"}>
              <Download className="h-3.5 w-3.5" /> Download document
            </a>
          </Button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function fade(reduceMotion: boolean | null) {
  return {
    initial: reduceMotion ? false : { opacity: 0, y: 4 },
    animate: { opacity: 1, y: 0 },
    exit: reduceMotion ? undefined : { opacity: 0, y: -4 },
    transition: { duration: 0.16, ease: "easeOut" as const },
  };
}
