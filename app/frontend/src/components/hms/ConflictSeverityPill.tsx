const toneFor: Record<string, string> = {
  low: "bg-muted text-muted-foreground border-border",
  moderate: "bg-info/10 text-info border-info/30",
  high: "bg-warning/10 text-warning border-warning/30",
  critical: "bg-destructive/10 text-destructive border-destructive/30",
};

export function ConflictSeverityPill({
  severity,
}: {
  severity: "low" | "moderate" | "high" | "critical";
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${toneFor[severity]}`}
    >
      {severity}
    </span>
  );
}
