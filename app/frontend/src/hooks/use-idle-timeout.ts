import { useEffect, useRef } from "react";

const EVENTS = ["mousemove", "keydown", "click", "scroll", "touchstart"] as const;

/** Fires onIdle after `ms` of no user activity. Pauses while tab is hidden. */
export function useIdleTimeout(ms: number, onIdle: () => void, enabled = true) {
  const cbRef = useRef(onIdle);
  cbRef.current = onIdle;

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    let timer: ReturnType<typeof setTimeout>;
    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(() => cbRef.current(), ms);
    };
    EVENTS.forEach((ev) => window.addEventListener(ev, reset, { passive: true }));
    reset();
    return () => {
      clearTimeout(timer);
      EVENTS.forEach((ev) => window.removeEventListener(ev, reset));
    };
  }, [ms, enabled]);
}