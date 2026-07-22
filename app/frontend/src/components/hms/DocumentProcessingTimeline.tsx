import type { DocumentProcessingEventRead } from "@/lib/api/documents";
import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

const stageLabel: Record<DocumentProcessingEventRead["stage"], string> = {
  upload: "Upload",
  ocr: "OCR",
  index: "Index",
  ready: "Ready",
};

export function DocumentProcessingTimeline({ events }: { events: DocumentProcessingEventRead[] }) {
  const reduceMotion = useReducedMotion();
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">Processing activity will appear here.</p>;
  }

  return (
    <ol className="space-y-3" aria-label="Document processing activity">
      {events.map((event) => {
        const label = `${stageLabel[event.stage]} ${event.state}`;
        const Icon =
          event.state === "completed"
            ? CheckCircle2
            : event.state === "failed"
              ? XCircle
              : CircleDashed;
        return (
          <motion.li
            key={event.id}
            className="flex gap-3 text-sm"
            initial={reduceMotion ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            <Icon
              className={`mt-0.5 h-4 w-4 shrink-0 ${
                event.state === "failed" ? "text-destructive" : "text-ai"
              }`}
              aria-hidden="true"
            />
            <div className="min-w-0">
              <p className="font-medium capitalize">{label}</p>
              <div className="flex flex-wrap gap-x-2 text-xs text-muted-foreground">
                <span>{new Date(event.created_at).toLocaleString()}</span>
                {event.progress_current !== null && event.progress_total !== null && (
                  <span>
                    {event.progress_current} / {event.progress_total}
                  </span>
                )}
                {event.error_code && (
                  <span className="font-mono text-destructive">{event.error_code}</span>
                )}
              </div>
            </div>
          </motion.li>
        );
      })}
    </ol>
  );
}
