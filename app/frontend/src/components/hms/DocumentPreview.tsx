import { useEffect, useState } from "react";
import { FileText, Loader2, Maximize2 } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { getDocumentBlob } from "@/lib/api/documents";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function DocumentPreview({
  documentId,
  mimeType,
}: {
  documentId: string;
  mimeType: string;
}) {
  const reduceMotion = useReducedMotion();
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let currentUrl: string | null = null;
    let active = true;
    setUrl(null);
    setFailed(false);
    getDocumentBlob(documentId)
      .then((blob) => {
        currentUrl = URL.createObjectURL(blob);
        if (active) {
          setUrl(currentUrl);
        } else {
          URL.revokeObjectURL(currentUrl);
        }
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [documentId]);

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
      ) : !url ? (
        <motion.div
          key="loading"
          className="flex items-center gap-2 text-sm text-muted-foreground"
          {...fade(reduceMotion)}
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading preview…
        </motion.div>
      ) : mimeType.startsWith("image/") ? (
        <motion.div key="image" className="relative group" {...fade(reduceMotion)}>
          <img
            src={url}
            alt="Document preview"
            className="max-h-[520px] w-full rounded border object-contain bg-muted/20"
          />
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="absolute -top-[42px] right-0 h-8 w-8 text-muted-foreground hover:text-foreground shadow-none z-10"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-[95vw] w-full max-h-[95vh] h-full p-2 flex flex-col border-none bg-background/95 backdrop-blur">
              <img src={url} alt="Fullscreen preview" className="w-full h-full object-contain" />
            </DialogContent>
          </Dialog>
        </motion.div>
      ) : mimeType === "application/pdf" ? (
        <motion.div key="pdf" className="relative group h-[520px]" {...fade(reduceMotion)}>
          <iframe title="Document preview" src={url} className="h-full w-full rounded border" />
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="absolute -top-[42px] right-0 h-8 w-8 text-muted-foreground hover:text-foreground shadow-none z-10"
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-[95vw] w-full max-h-[95vh] h-[95vh] p-0 overflow-hidden border-none">
              <iframe src={url} className="w-full h-full" title="Fullscreen Document" />
            </DialogContent>
          </Dialog>
        </motion.div>
      ) : (
        <motion.a
          key="download"
          className="inline-flex items-center gap-2 text-sm text-ai underline"
          href={url}
          download
          {...fade(reduceMotion)}
        >
          <FileText className="h-4 w-4" /> Download document
        </motion.a>
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
