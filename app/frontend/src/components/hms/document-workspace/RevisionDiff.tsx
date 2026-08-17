import { useEffect, useMemo, useRef, useState } from "react";
import { computeTextDiff, type DiffRow, type WordPart } from "@/lib/text-diff";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Columns2,
  FileQuestion,
  PencilLine,
  Rows2,
} from "lucide-react";

type DiffView = "split" | "unified";

const CHANGED_WORD_STYLES = {
  removed: "rounded-[2px] bg-rose-500/25 px-[1px] font-medium text-rose-800 dark:text-rose-200",
  added:
    "rounded-[2px] bg-emerald-500/25 px-[1px] font-medium text-emerald-800 dark:text-emerald-300",
} as const;

function plural(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}

function WordSpan({ part, side }: { part: WordPart; side: "removed" | "added" }) {
  if (!part.changed) return <>{part.value}</>;
  return (
    <span data-diff={`${side}-word`} className={CHANGED_WORD_STYLES[side]}>
      {part.value}
    </span>
  );
}

function LineNumbers({ left, right }: { left?: number; right?: number }) {
  return (
    <span
      aria-hidden="true"
      className="w-7 shrink-0 select-none pr-1.5 text-right font-mono text-[10px] leading-relaxed text-muted-foreground/60"
    >
      {left ?? right ?? ""}
    </span>
  );
}

const TEXT_STYLES =
  "min-w-0 flex-1 whitespace-pre-wrap break-words font-mono text-xs leading-relaxed [overflow-wrap:anywhere]";

export function RevisionDiff({
  originalText,
  correctedText,
  hasUnsavedEdits = false,
}: {
  originalText: string;
  correctedText: string;
  hasUnsavedEdits?: boolean;
}) {
  const [view, setView] = useState<DiffView>("split");
  const [navIndex, setNavIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const { rows, stats } = useMemo(
    () => computeTextDiff(originalText, correctedText),
    [originalText, correctedText],
  );

  const changeRowIndexes = useMemo(() => {
    const indexes: number[] = [];
    rows.forEach((row, index) => {
      if (row.type === "equal") return;
      if (index === 0 || rows[index - 1].type === "equal") indexes.push(index);
    });
    return indexes;
  }, [rows]);

  useEffect(() => {
    setNavIndex(0);
  }, [originalText, correctedText]);

  const goToChange = (index: number) => {
    if (changeRowIndexes.length === 0) return;
    const next = (index + changeRowIndexes.length) % changeRowIndexes.length;
    setNavIndex(next);
    const rowIndex = changeRowIndexes[next];
    const target = containerRef.current?.querySelector(`[data-diff-row="${rowIndex}"]`);
    const reduceMotion =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    target?.scrollIntoView?.({ block: "center", behavior: reduceMotion ? "auto" : "smooth" });
  };

  const hasChanges = changeRowIndexes.length > 0;
  const hasNoText = !originalText.trim() && !correctedText.trim();
  const similarityPercent =
    stats.similarity >= 1 ? "100%" : `${(stats.similarity * 100).toFixed(1)}%`;

  return (
    <div className="flex flex-1 flex-col h-full min-h-0 overflow-hidden rounded-xl border border-border/80 bg-card">
      <div className="flex flex-wrap items-center gap-2 select-none border-b border-border/70 bg-muted/30 px-3 py-2">
        <div className="flex flex-wrap items-center gap-1.5" aria-hidden="true">
          {stats.addedLines > 0 && (
            <span className="rounded-md bg-emerald-500/15 px-1.5 py-0.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
              +{plural(stats.addedLines, "addition")}
            </span>
          )}
          {stats.removedLines > 0 && (
            <span className="rounded-md bg-rose-500/15 px-1.5 py-0.5 text-[11px] font-medium text-rose-700 dark:text-rose-300">
              &minus;{plural(stats.removedLines, "deletion")}
            </span>
          )}
          {stats.modifiedLines > 0 && (
            <span className="rounded-md bg-amber-500/15 px-1.5 py-0.5 text-[11px] font-medium text-amber-700 dark:text-amber-300">
              ±{plural(stats.modifiedLines, "modification")}
            </span>
          )}
          <span className="rounded-md bg-muted/70 px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
            {similarityPercent} match
          </span>
        </div>

        {hasUnsavedEdits && (
          <span className="flex items-center gap-1 text-[11px] font-medium text-amber-600 dark:text-amber-400">
            <PencilLine className="h-3 w-3" />
            Unsaved edits included
          </span>
        )}

        <div className="ml-auto flex items-center gap-2">
          {hasChanges && (
            <div className="flex items-center gap-0.5">
              <button
                type="button"
                aria-label="Previous change"
                onClick={() => goToChange(navIndex - 1)}
                className="grid h-6 w-6 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <ChevronUp className="h-3.5 w-3.5" />
              </button>
              <span
                role="status"
                className="min-w-10 text-center text-[11px] tabular-nums text-muted-foreground"
              >
                {navIndex + 1} / {changeRowIndexes.length}
              </span>
              <button
                type="button"
                aria-label="Next change"
                onClick={() => goToChange(navIndex + 1)}
                className="grid h-6 w-6 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          <div
            role="group"
            aria-label="Diff view mode"
            className="flex h-7 rounded-lg bg-muted/50 p-0.5"
          >
            <button
              type="button"
              aria-pressed={view === "split"}
              onClick={() => setView("split")}
              className={`flex h-6 items-center gap-1 rounded-md px-2 text-xs font-medium transition-colors ${
                view === "split"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Columns2 className="h-3.5 w-3.5" />
              Split
            </button>
            <button
              type="button"
              aria-pressed={view === "unified"}
              onClick={() => setView("unified")}
              className={`flex h-6 items-center gap-1 rounded-md px-2 text-xs font-medium transition-colors ${
                view === "unified"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Rows2 className="h-3.5 w-3.5" />
              Unified
            </button>
          </div>
        </div>
      </div>

      <span className="sr-only" role="status">
        {plural(stats.addedLines, "line added")}, {plural(stats.removedLines, "line removed")},{" "}
        {plural(stats.modifiedLines, "line modified")}
      </span>

      {hasNoText ? (
        <div className="grid flex-1 place-items-center p-6">
          <div className="flex max-w-sm flex-col items-center gap-2 text-center">
            <FileQuestion className="h-8 w-8 text-muted-foreground/60" />
            <p className="text-sm font-medium text-foreground">No text available for this page</p>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Run OCR or load a corrected revision to compare versions here.
            </p>
          </div>
        </div>
      ) : !hasChanges ? (
        <div className="grid flex-1 place-items-center p-6">
          <div className="flex max-w-sm flex-col items-center gap-2 text-center">
            <div className="grid h-10 w-10 place-items-center rounded-full bg-emerald-500/10">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            </div>
            <p className="text-sm font-medium text-foreground">
              Corrected text matches the original
            </p>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Edits you make in the Corrected tab are highlighted here as you type.
            </p>
          </div>
        </div>
      ) : (
        <>
          {view === "split" ? (
            <div className="grid grid-cols-2 select-none border-b border-border/70 bg-muted/20">
              <div className="flex items-center justify-between px-3 py-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Original OCR
                </span>
                <span className="rounded bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                  Baseline
                </span>
              </div>
              <div className="flex items-center justify-between border-l border-border/60 px-3 py-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-primary">
                  Corrected Text
                </span>
                <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                  Active Version
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 border-b border-border/70 bg-muted/20 px-3 py-1.5 select-none">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Unified diff
              </span>
              <span className="text-[10px] text-muted-foreground">
                <span className="font-medium text-rose-600 dark:text-rose-400">
                  &minus; removed
                </span>
                <span className="mx-1.5" aria-hidden="true">
                  ·
                </span>
                <span className="font-medium text-emerald-600 dark:text-emerald-400">+ added</span>
              </span>
            </div>
          )}

          <div ref={containerRef} className="flex-1 min-h-0">
            <ScrollArea className="h-full">
              <div className="min-w-0">
                {view === "split"
                  ? rows.map((row, index) => <SplitRow key={index} row={row} index={index} />)
                  : rows.map((row, index) => <UnifiedRow key={index} row={row} index={index} />)}
              </div>
            </ScrollArea>
          </div>
        </>
      )}
    </div>
  );
}

function SplitRow({ row, index }: { row: DiffRow; index: number }) {
  const leftCellClass =
    row.type === "modified" || row.type === "removed" ? "bg-rose-500/[0.08]" : "";
  const rightCellClass =
    row.type === "modified" || row.type === "added" ? "bg-emerald-500/[0.08]" : "";
  const mutedText = row.type === "equal" ? "text-foreground/75" : "text-foreground";

  return (
    <div data-diff-row={index} className="flex items-start">
      <div className={`flex w-1/2 min-w-0 items-start px-2 py-[3px] ${leftCellClass}`}>
        {row.type === "added" ? (
          <div className="h-4 flex-1 rounded-sm bg-muted/30" aria-hidden="true" />
        ) : (
          <>
            <LineNumbers left={row.leftNumber} />
            <span className={`${TEXT_STYLES} ${mutedText}`}>
              {row.type === "modified"
                ? row.leftParts.map((part, partIndex) => (
                    <WordSpan key={partIndex} part={part} side="removed" />
                  ))
                : row.left}
            </span>
          </>
        )}
      </div>
      <div className="w-px shrink-0 self-stretch bg-border/50" aria-hidden="true" />
      <div className={`flex min-w-0 flex-1 items-start px-2 py-[3px] ${rightCellClass}`}>
        {row.type === "removed" ? (
          <div className="h-4 flex-1 rounded-sm bg-muted/30" aria-hidden="true" />
        ) : (
          <>
            <LineNumbers right={row.rightNumber} />
            <span className={`${TEXT_STYLES} ${mutedText}`}>
              {row.type === "modified"
                ? row.rightParts.map((part, partIndex) => (
                    <WordSpan key={partIndex} part={part} side="added" />
                  ))
                : row.right}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

function UnifiedRow({ row, index }: { row: DiffRow; index: number }) {
  const entries: Array<{
    marker: string;
    markerClass: string;
    rowClass: string;
    number: number;
    content: React.ReactNode;
  }> = [];

  if (row.type === "equal") {
    entries.push({
      marker: "",
      markerClass: "text-transparent",
      rowClass: "text-foreground/75",
      number: row.rightNumber,
      content: row.right,
    });
  } else if (row.type === "removed") {
    entries.push({
      marker: "\u2212",
      markerClass: "text-rose-600 dark:text-rose-400",
      rowClass: "bg-rose-500/[0.08]",
      number: row.leftNumber,
      content: row.left,
    });
  } else if (row.type === "added") {
    entries.push({
      marker: "+",
      markerClass: "text-emerald-600 dark:text-emerald-400",
      rowClass: "bg-emerald-500/[0.08]",
      number: row.rightNumber,
      content: row.right,
    });
  } else {
    entries.push(
      {
        marker: "\u2212",
        markerClass: "text-rose-600 dark:text-rose-400",
        rowClass: "bg-rose-500/[0.08]",
        number: row.leftNumber,
        content: row.leftParts.map((part, partIndex) => (
          <WordSpan key={partIndex} part={part} side="removed" />
        )),
      },
      {
        marker: "+",
        markerClass: "text-emerald-600 dark:text-emerald-400",
        rowClass: "bg-emerald-500/[0.08]",
        number: row.rightNumber,
        content: row.rightParts.map((part, partIndex) => (
          <WordSpan key={partIndex} part={part} side="added" />
        )),
      },
    );
  }

  return (
    <>
      {entries.map((entry, entryIndex) => (
        <div
          key={entryIndex}
          data-diff-row={index}
          data-diff-marker={entry.marker.trim()}
          className={`flex items-start px-2 py-[3px] ${entry.rowClass}`}
        >
          <span
            aria-hidden="true"
            className={`w-5 shrink-0 select-none text-center font-mono text-[11px] leading-relaxed ${entry.markerClass}`}
          >
            {entry.marker}
          </span>
          <LineNumbers left={entry.number} />
          <span className={TEXT_STYLES}>{entry.content}</span>
        </div>
      ))}
    </>
  );
}
