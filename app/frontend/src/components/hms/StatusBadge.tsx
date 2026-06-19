import { cn } from "@/lib/utils";

type Status =
  | "indexed"
  | "processing"
  | "queued"
  | "ocr"
  | "error"
  | "allow"
  | "deny"
  | "pending"
  | "success";

const map: Record<Status, { label: string; cls: string; dot: string }> = {
  indexed: {
    label: "Indexed",
    cls: "bg-success/10 text-success border-success/20",
    dot: "bg-success",
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
};

export function StatusBadge({
  status,
  label,
  className,
}: {
  status: Status;
  label?: string;
  className?: string;
}) {
  const m = map[status];
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
