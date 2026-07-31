import type { DocumentProcessingEventRead } from "@/lib/api/documents";
import { CheckCircle2, CircleDashed, XCircle } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { TypewriterText } from "@/components/ui/typewriter";

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
    <div className="overflow-x-auto pb-2 -mx-2 px-2">
      <ol
        className="flex items-start w-full min-w-max gap-4"
        aria-label="Document processing activity"
      >
        {events.map((event, index) => {
          const label = `${stageLabel[event.stage]} ${event.state}`;
          const Icon =
            event.state === "completed"
              ? CheckCircle2
              : event.state === "failed"
                ? XCircle
                : CircleDashed;

          const isLast = index === events.length - 1;
          const delay = index * 0.15; // increased delay to stagger the typing

          const dateStr = new Date(event.created_at).toLocaleString(undefined, {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });

          return (
            <motion.li
              key={event.id}
              className={`flex flex-col relative text-sm w-[130px] shrink-0`}
              initial={reduceMotion ? false : { opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.18, ease: "easeOut", delay: index * 0.05 }}
            >
              <div className="flex items-center w-full mb-2">
                <Icon
                  className={`h-5 w-5 shrink-0 z-10 bg-card ${
                    event.state === "failed" ? "text-destructive" : "text-ai"
                  }`}
                  aria-hidden="true"
                />
                {!isLast && <div className="h-[2px] flex-1 bg-border ml-2" />}
              </div>

              <div className="pr-2">
                <TypewriterText
                  text={label}
                  delay={delay * 1000}
                  speed={1}
                  className="font-medium capitalize text-xs mb-1 line-clamp-1"
                />
                <div className="flex flex-col gap-0.5 text-[10px] text-muted-foreground">
                  <TypewriterText
                    text={dateStr}
                    delay={delay * 1000 + 200}
                    speed={1}
                    className="truncate"
                  />
                  {event.progress_current !== null && event.progress_total !== null && (
                    <TypewriterText
                      text={`${event.progress_current} / ${event.progress_total}`}
                      delay={delay * 1000 + 400}
                      speed={1}
                    />
                  )}
                  {event.error_code && (
                    <TypewriterText
                      text={event.error_code}
                      delay={delay * 1000 + 400}
                      speed={1}
                      className="font-mono text-destructive truncate"
                    />
                  )}
                </div>
              </div>
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}
