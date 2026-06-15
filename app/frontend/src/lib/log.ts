import type { AppErrorCode } from "./errors";

export interface LogEntry {
  id: string;
  ts: string;
  level: "info" | "warn" | "error";
  code?: AppErrorCode;
  message: string;
  context?: Record<string, unknown>;
}

const buffer: LogEntry[] = [];
const MAX = 100;
const listeners = new Set<(e: LogEntry) => void>();

function push(entry: LogEntry) {
  buffer.unshift(entry);
  if (buffer.length > MAX) buffer.pop();
  listeners.forEach((l) => l(entry));
}

export function logError(err: unknown, context?: Record<string, unknown>) {
  const message = err instanceof Error ? err.message : String(err);
  const entry: LogEntry = {
    id: `evt-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
    ts: new Date().toISOString(),
    level: "error",
    code: context?.code as AppErrorCode | undefined,
    message,
    context,
  };
  // eslint-disable-next-line no-console
  console.error("[hms]", entry.code ?? "error", message, context ?? "");
  push(entry);
  return entry;
}

export function logInfo(message: string, context?: Record<string, unknown>) {
  const entry: LogEntry = {
    id: `evt-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
    ts: new Date().toISOString(),
    level: "info",
    message,
    context,
  };
  push(entry);
  return entry;
}

export function getRecentLogs(): LogEntry[] {
  return [...buffer];
}

export function subscribeLogs(fn: (e: LogEntry) => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}