import { useCallback, useEffect, useRef, useState } from "react";
import { logError } from "@/lib/log";
import type { StreamStatus } from "./use-stream-text";

interface Options {
  intervalMs?: number;
  forceInterrupt?: boolean;
  failureRate?: number;
  failureReason?: string;
}

/**
 * Mock progressive reveal for ordered, discrete items (graph paths, traces, plan steps).
 * Mirrors `useStreamText`'s abort/retry/resume controls.
 */
export function useStreamSteps(totalSteps: number, options: Options = {}) {
  const {
    intervalMs = 420,
    forceInterrupt = false,
    failureRate = 0,
    failureReason = "Reasoning stream interrupted by upstream timeout.",
  } = options;

  const [revealed, setRevealed] = useState(0);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [error, setError] = useState<string | undefined>();
  const failAt = useRef<number | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const clear = () => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  };

  const run = useCallback(
    (from: number) => {
      clear();
      setError(undefined);
      setRevealed(from);
      setStatus(from >= totalSteps ? "complete" : "streaming");
      if (forceInterrupt) failAt.current = Math.max(1, Math.ceil(totalSteps * 0.5));
      else if (failureRate > 0 && Math.random() < failureRate) failAt.current = Math.max(1, Math.floor(Math.random() * totalSteps));
      else failAt.current = null;

      let i = from;
      timer.current = setInterval(() => {
        if (failAt.current !== null && i >= failAt.current) {
          clear();
          logError("ai.reasoning_interrupted", { reason: failureReason, step: i });
          setStatus("interrupted");
          setError(failureReason);
          return;
        }
        i += 1;
        setRevealed(i);
        if (i >= totalSteps) {
          clear();
          setStatus("complete");
        }
      }, intervalMs);
    },
    [totalSteps, intervalMs, forceInterrupt, failureRate, failureReason],
  );

  useEffect(() => () => clear(), []);

  return {
    revealed,
    status,
    error,
    progress: revealed,
    total: totalSteps,
    start: useCallback(() => run(0), [run]),
    retry: useCallback(() => run(0), [run]),
    resume: useCallback(() => run(revealed), [run, revealed]),
    stop: useCallback(() => {
      clear();
      setStatus("interrupted");
      // Preserve any prior interruption reason on repeated Stop clicks.
      setError((prev) => prev ?? "Stopped by user.");
    }, []),
  };
}