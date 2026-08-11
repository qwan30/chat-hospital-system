import { cn } from "@/lib/utils";

type Status =
  | "indexed"
  | "ready"
  | "ready_with_warnings"
  | "processing"
  | "queued"
  | "ocr"
  | "error"
  | "allow"
  | "deny"
  | "pending"
  | "success"
  // The remaining seven members of the documents.status check constraint
  // (db/models.py:157-158). Without these, a failed document rendered through
  // the generic fallback as a neutral grey badge -- visually identical to a
  // benign "Uploaded" -- even though dashboard.py:67 counts ocr_failed and
  // index_failed as the `failed` metric.
  | "uploaded"
  | "ocr_processing"
  | "ocr_failed"
  | "ocr_completed"
  | "indexing"
  | "index_failed"
  | "archived";

const map: Record<Status, { label: string; cls: string; dot: string }> = {
  indexed: {
    label: "Indexed",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
  },
  ready: {
    label: "Ready",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
  },
  ready_with_warnings: {
    label: "Ready with warnings",
    cls: "bg-warning/10 text-warning border-warning/20",
    dot: "bg-warning",
  },
  processing: {
    label: "Processing",
    cls: "bg-info/10 text-info border-info/20",
    dot: "bg-info animate-pulse",
  },
  queued: {
    label: "Queued",
    cls: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  },
  ocr: { label: "OCR", cls: "bg-ai/10 text-ai border-ai/20", dot: "bg-ai animate-pulse" },
  error: {
    label: "Error",
    cls: "bg-destructive/10 text-destructive border-destructive/20",
    dot: "bg-destructive",
  },
  allow: {
    label: "Allowed",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
  },
  deny: {
    label: "Denied",
    cls: "bg-destructive/10 text-destructive border-destructive/20",
    dot: "bg-destructive",
  },
  pending: {
    label: "Pending",
    cls: "bg-warning/10 text-warning border-warning/20",
    dot: "bg-warning",
  },
  success: {
    label: "Success",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
  },

  // documents.status vocabulary (db/models.py:157-158). The two *_failed states
  // reuse the destructive treatment so a failed document reads as failed here,
  // matching _app.patients.$patientId.documents.tsx:87.
  uploaded: {
    label: "Uploaded",
    cls: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  },
  ocr_processing: {
    label: "OCR Processing",
    cls: "bg-info/10 text-info border-info/20",
    dot: "bg-info animate-pulse",
  },
  ocr_failed: {
    label: "OCR Failed",
    cls: "bg-destructive/10 text-destructive border-destructive/20",
    dot: "bg-destructive",
  },
  ocr_completed: {
    label: "OCR Completed",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
  },
  indexing: {
    label: "Indexing",
    cls: "bg-info/10 text-info border-info/20",
    dot: "bg-info animate-pulse",
  },
  index_failed: {
    label: "Index Failed",
    cls: "bg-destructive/10 text-destructive border-destructive/20",
    dot: "bg-destructive",
  },
  archived: {
    label: "Archived",
    cls: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  },
};

/** Title-case an unmapped backend status: "ocr_failed" -> "Ocr Failed". */
function humanizeStatus(status: string): string {
  return status
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function StatusBadge({
  status,
  label,
  className,
}: {
  status: Status | (string & {});
  label?: string;
  className?: string;
}) {
  // The backend's status vocabulary is broader than this map: `ocr_failed` is
  // returned by /documents today and had no entry here, so `map[status]` was
  // undefined and reading `.cls` threw, blanking the whole Documents page with
  // "Something went wrong". Any status now renders rather than crashing the
  // surrounding route -- unknown values degrade to a neutral badge.
  const m = map[status as Status] ?? {
    label: humanizeStatus(status),
    cls: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        m.cls,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", m.dot)} />
      {label ?? m.label}
    </span>
  );
}
