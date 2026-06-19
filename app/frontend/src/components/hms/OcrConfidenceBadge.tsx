export function OcrConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const tone =
    confidence >= 0.9
      ? "bg-success/10 text-success border-success/30"
      : confidence >= 0.7
        ? "bg-warning/10 text-warning border-warning/30"
        : "bg-destructive/10 text-destructive border-destructive/30";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-xs ${tone}`}
    >
      {pct}%
    </span>
  );
}
