import { useEffect, useState } from "react";
import { FileText, Loader2 } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { getDocumentBlob } from "@/lib/api/documents";

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
        <motion.img
          key="image"
          src={url}
          alt="Document preview"
          className="max-h-[520px] w-full rounded border object-contain"
          {...fade(reduceMotion)}
        />
      ) : mimeType === "application/pdf" ? (
        <motion.iframe
          key="pdf"
          title="Document preview"
          src={url}
          className="h-[520px] w-full rounded border"
          {...fade(reduceMotion)}
        />
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
