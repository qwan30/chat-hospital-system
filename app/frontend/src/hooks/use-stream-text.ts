import { useCallback, useEffect, useRef, useState } from "react";
import { logError } from "@/lib/log";

export type StreamStatus = "idle" | "streaming" | "interrupted" | "complete";

export interface StreamState {
  text: string;
  status: StreamStatus;
  error?: string;
  /** number of characters successfully delivered */
  progress: number;
}

interface Options {
  /** Token chunk size (chars per tick). */
  chunkSize?: number;
  /** Tick interval in ms. */
  intervalMs?: number;
  /**
   * If true, force an interruption at ~40% (used for `?simulate=stream-fail`).
   * Otherwise a small random chance applies.
   */
  forceInterrupt?: boolean;
  /** Probability of random interruption per stream (0–1). */
  failureRate?: number;
  /** Reason label rendered in the interrupted banner. */
  failureReason?: string;
  onComplete?: (finalText: string) => void;
}

/**
 * Mock token stream with abort, retry-from-scratch, and resume-from-cursor.
 * Designed for AI/RAG views that need to demo streaming interruption UX.
 */
export function useStreamText(fullText: string, options: Options = {}) {
  const {
    chunkSize = 4,
    intervalMs = 28,
    forceInterrupt = false,
    failureRate = 0,
    failureReason = "Connection to LLM runtime dropped mid-stream.",
    onComplete,
  } = options;

  const [state, setState] = useState<StreamState>({
    text: "",
    status: "idle",
    progress: 0,
  });
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const willFail = useRef<number | null>(null);

  const clear = () => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  };

  const run = useCallback(
    (from: number) => {
      clear();
      // Decide a failure cursor for this run.
      if (forceInterrupt) {
        willFail.current = Math.floor(fullText.length * 0.4);
      } else if (failureRate > 0 && Math.random() < failureRate) {
        willFail.current = Math.floor(fullText.length * (0.3 + Math.random() * 0.5));
      } else {
        willFail.current = null;
      }

      setState((s) => ({ ...s, status: "streaming", error: undefined, progress: from, text: fullText.slice(0, from) }));

      let cursor = from;
      timer.current = setInterval(() => {
        if (willFail.current !== null && cursor >= willFail.current) {
          clear();
          logError("ai.stream_interrupted", { reason: failureReason, cursor });
          setState({
            text: fullText.slice(0, cursor),
            status: "interrupted",
            error: failureReason,
            progress: cursor,
          });
          return;
        }
        cursor = Math.min(fullText.length, cursor + chunkSize);
        setState({
          text: fullText.slice(0, cursor),
          status: cursor >= fullText.length ? "complete" : "streaming",
          progress: cursor,
        });
        if (cursor >= fullText.length) {
          clear();
          onComplete?.(fullText);
        }
      }, intervalMs);
    },
    [fullText, chunkSize, intervalMs, forceInterrupt, failureRate, failureReason, onComplete],
  );

  useEffect(() => () => clear(), []);

  const start = useCallback(() => run(0), [run]);
  const retry = useCallback(() => run(0), [run]);
  const resume = useCallback(() => run(state.progress), [run, state.progress]);
  const stop = useCallback(() => {
    clear();
    setState((s) => ({
      ...s,
      status: "interrupted",
      // Preserve the original failure reason if the stream was already
      // interrupted — repeated Stop clicks should be a no-op.
      error: s.status === "interrupted" ? s.error : "Stopped by user.",
    }));
  }, []);

  return { ...state, start, retry, resume, stop };
}